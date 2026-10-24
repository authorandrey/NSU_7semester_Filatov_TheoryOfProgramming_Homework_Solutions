#!/usr/bin/env python3
"""Translate a RAM assembly file with `call LABEL` and `ret` into ordinary RAM assembly."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
TOKEN_RE = re.compile(r"^-?\d+$")

SUPPORTED = {
    "halt": "Halt",
    "load": "Load",
    "store": "Store",
    "add": "Add",
    "sub": "Sub",
    "mult": "Mult",
    "div": "Div",
    "read": "Read",
    "write": "Write",
    "jump": "Jump",
    "jzero": "JZero",
    "jgtz": "JGTZ",
}


class TranslationError(Exception):
    pass


@dataclass
class SourceNode:
    labels: list[str] = field(default_factory=list)
    op: str = ""
    arg: str = ""
    comment: str = ""
    line_no: int = 0


@dataclass
class OutInstr:
    op: str
    arg: str
    label: Optional[str] = None
    comment: str = ""


def parse_source(source: str) -> list[SourceNode]:
    nodes: list[SourceNode] = []
    pending_labels: list[tuple[str, int]] = []
    defined: set[str] = set()

    for line_no, original in enumerate(source.splitlines(), start=1):
        code, sep, comment = original.partition(";")
        code = code.strip()
        comment = comment.strip() if sep else ""
        labels_on_line: list[str] = []

        while code:
            match = LABEL_RE.match(code)
            if not match:
                break
            label, code = match.group(1), match.group(2).strip()
            if label in defined or any(label == known for known, _ in pending_labels):
                raise TranslationError(f"line {line_no}: duplicate label {label!r}")
            defined.add(label)
            labels_on_line.append(label)

        if not code:
            pending_labels.extend((label, line_no) for label in labels_on_line)
            continue

        parts = code.split()
        op_raw = parts[0]
        op_key = op_raw.lower()
        labels = [label for label, _ in pending_labels] + labels_on_line
        pending_labels.clear()

        if op_key in {"call", "ret", "return"}:
            if op_key == "call":
                if len(parts) != 2:
                    raise TranslationError(f"line {line_no}: syntax is 'call LABEL'")
                op, arg = "call", parts[1]
            else:
                if len(parts) != 1:
                    raise TranslationError(f"line {line_no}: syntax is '{op_raw}' without an argument")
                op, arg = "ret", ""
        else:
            if op_key not in SUPPORTED:
                raise TranslationError(f"line {line_no}: unsupported instruction {op_raw!r}")
            if len(parts) != 2:
                raise TranslationError(f"line {line_no}: syntax is '{op_raw} ARGUMENT'")
            op, arg = SUPPORTED[op_key], parts[1]
            if op in {"Jump", "JZero", "JGTZ"} and (arg.startswith("=") or arg.startswith("*")):
                raise TranslationError(f"line {line_no}: {op} requires a direct label/address, got {arg!r}")

        nodes.append(SourceNode(labels, op, arg, comment, line_no))

    if pending_labels:
        # A label at end-of-file is given a concrete, safe target.
        nodes.append(SourceNode([label for label, _ in pending_labels], "Halt", "0", "end label", pending_labels[0][1]))

    if not nodes:
        raise TranslationError("input file contains no instructions")

    all_labels: set[str] = set()
    for node in nodes:
        for label in node.labels:
            if label in all_labels:
                raise TranslationError(f"line {node.line_no}: duplicate label {label!r}")
            all_labels.add(label)

    for node in nodes:
        if node.op in {"Jump", "JZero", "JGTZ"} and not TOKEN_RE.fullmatch(node.arg):
            if node.arg not in all_labels:
                raise TranslationError(f"line {node.line_no}: undefined jump label {node.arg!r}")
        if node.op == "call" and node.arg not in all_labels:
            raise TranslationError(f"line {node.line_no}: undefined call target {node.arg!r}")

    if any(node.op == "ret" for node in nodes) and not any(node.op == "call" for node in nodes):
        raise TranslationError("'ret' is used, but the program contains no 'call' sites")

    return nodes


def choose_stack_base(nodes: list[SourceNode], requested: Optional[int]) -> int:
    if requested is not None:
        if requested < 2:
            raise TranslationError("--stack-base must be at least 2 (cell 1 is reserved by the call convention)")
        return requested

    # Avoid all explicit numeric literals with a generous gap. This is a default,
    # not a proof against a program that dynamically indexes into the stack area.
    largest = 0
    for node in nodes:
        for token in re.findall(r"(?<![A-Za-z_])-?\d+", node.arg):
            try:
                largest = max(largest, abs(int(token)))
            except ValueError:
                pass
    return max(10_000, largest + 1_024)


def emit_with_labels(labels: list[str], instructions: list[OutInstr]) -> list[OutInstr]:
    """Attach source labels, preserving multiple label-only aliases with harmless jumps."""
    if not instructions:
        instructions = [OutInstr("Halt", "0")]
    if not labels:
        return instructions

    prefix: list[OutInstr] = []
    for i, label in enumerate(labels[:-1]):
        prefix.append(OutInstr("Jump", labels[i + 1], label=label, comment="label alias"))
    instructions[0].label = labels[-1]
    return prefix + instructions


def translate(source: str, stack_base: Optional[int] = None) -> tuple[str, dict[str, int]]:
    nodes = parse_source(source)
    stack_base = choose_stack_base(nodes, stack_base)
    sp_cell = stack_base - 1

    user_labels = {label for node in nodes for label in node.labels}
    prefix = "__CALLGEN"
    while any(label.startswith(prefix) for label in user_labels):
        prefix += "_X"

    def gen(name: str) -> str:
        return f"{prefix}_{name}"

    # Map numeric source jump targets to synthetic labels before expansion.
    # A numeric target refers to a source instruction (a call/ret pseudo-op counts as one).
    source_pc_labels = [gen(f"SRC_PC_{i}") for i in range(1, len(nodes) + 1)]
    for node in nodes:
        if node.op in {"Jump", "JZero", "JGTZ"} and TOKEN_RE.fullmatch(node.arg):
            target = int(node.arg)
            if target < 1 or target > len(nodes):
                raise TranslationError(
                    f"line {node.line_no}: numeric jump target {target} is outside source instruction range 1..{len(nodes)}"
                )
            node.arg = source_pc_labels[target - 1]

    calls = [node for node in nodes if node.op == "call"]
    has_return = any(node.op == "ret" for node in nodes)
    after_labels = [gen(f"AFTER_{i}") for i in range(len(calls))]
    match_labels = [gen(f"MATCH_{i}") for i in range(len(calls))]
    return_dispatch = gen("RETURN_DISPATCH")
    invalid_return = gen("INVALID_RETURN")
    entry_label = gen("ENTRY")
    user_body_label = gen("USER_BODY")
    program_end = gen("PROGRAM_END")

    out: list[OutInstr] = [
        OutInstr("Load", f"={stack_base}", comment="initialize call stack pointer"),
        OutInstr("Store", str(sp_cell), comment="reserved stack pointer cell"),
        OutInstr("Jump", entry_label, comment="enter translated program"),
        OutInstr("Jump", user_body_label, label=entry_label, comment="entry trampoline"),
    ]

    call_index = 0
    first_user_node = True
    for node_index, node in enumerate(nodes):
        labels = [source_pc_labels[node_index]] + list(node.labels)
        if first_user_node:
            labels.insert(0, user_body_label)
            first_user_node = False

        if node.op == "call":
            idx = call_index
            call_index += 1
            seq = [
                OutInstr("Load", "1", comment="save caller's return address"),
                OutInstr("Store", f"*{sp_cell}", comment="push R1 onto the call stack"),
                OutInstr("Load", str(sp_cell)),
                OutInstr("Add", "=1"),
                OutInstr("Store", str(sp_cell), comment="advance stack pointer"),
                OutInstr("Load", f"@RETADDR:{idx}@", comment="R1 := address after this call"),
                OutInstr("Store", "1"),
                OutInstr("Jump", node.arg, comment=f"call {node.arg}"),
                OutInstr("Store", "10", label=after_labels[idx], comment="save return value in volatile R10"),
                OutInstr("Load", str(sp_cell)),
                OutInstr("Sub", "=1"),
                OutInstr("Store", str(sp_cell), comment="pop previous return address"),
                OutInstr("Load", f"*{sp_cell}"),
                OutInstr("Store", "1", comment="restore caller's R1"),
                OutInstr("Load", "10", comment="restore function result in R0"),
            ]
        elif node.op == "ret":
            seq = [OutInstr("Jump", return_dispatch, comment="return via generated dispatch table")]
        else:
            seq = [OutInstr(node.op, node.arg, comment=node.comment)]

        out.extend(emit_with_labels(labels, seq))

    # Prevent normal fall-through into the generated return dispatcher.
    out.append(OutInstr("Jump", program_end, comment="skip generated return dispatcher"))

    if has_return:
        out.append(OutInstr("Store", "10", label=return_dispatch, comment="save function result while checking R1"))
        for i, after in enumerate(after_labels):
            out.append(OutInstr("Load", "1"))
            out.append(OutInstr("Sub", f"@RETADDR:{i}@"))
            out.append(OutInstr("JZero", match_labels[i]))
        out.append(OutInstr("Jump", invalid_return, comment="unknown return address"))

        for i, after in enumerate(after_labels):
            out.append(OutInstr("Load", "10", label=match_labels[i], comment="restore function result"))
            out.append(OutInstr("Jump", after))

        out.append(OutInstr("Halt", "0", label=invalid_return, comment="invalid return address"))

    out.append(OutInstr("Halt", "0", label=program_end, comment="program end"))

    # Pass 1: resolve labels to RAM instruction numbers (1-based).
    labels_to_pc: dict[str, int] = {}
    pc = 1
    for instruction in out:
        if instruction.label:
            if instruction.label in labels_to_pc:
                raise TranslationError(f"generated duplicate label {instruction.label!r}")
            labels_to_pc[instruction.label] = pc
        pc += 1

    # Pass 2: materialize return addresses into numeric constants in R1 and dispatch tests.
    rendered: list[str] = []
    for instruction in out:
        arg = instruction.arg
        placeholder = re.fullmatch(r"@RETADDR:(\d+)@", arg)
        if placeholder:
            idx = int(placeholder.group(1))
            target = after_labels[idx]
            arg = str(labels_to_pc[target])
            if instruction.op in {"Load", "Sub"}:
                arg = "=" + arg
        line = f"{instruction.label + ': ' if instruction.label else ''}{instruction.op} {arg}"
        if instruction.comment:
            line += f" ; {instruction.comment}"
        rendered.append(line)

    return "\n".join(rendered) + "\n", labels_to_pc


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Translate RAM assembly with 'call LABEL' and 'ret' into ordinary RAM assembly."
    )
    parser.add_argument("input", type=Path, help="input .tur_call file")
    parser.add_argument("-o", "--output", type=Path, help="output .tur file (default: input with .tur suffix)")
    parser.add_argument(
        "--stack-base", type=int, default=None,
        help="first memory cell used for the generated call stack (default: auto-selected; keep this region free)",
    )
    args = parser.parse_args(argv)

    input_path: Path = args.input
    if not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    output_path = args.output if args.output is not None else input_path.with_suffix(".tur")

    try:
        source = input_path.read_text(encoding="utf-8-sig")
        translated, labels = translate(source, args.stack_base)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(translated, encoding="utf-8")
    except (OSError, UnicodeError, TranslationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    call_count = sum(1 for line in source.splitlines() if re.match(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*:\s*)?call\s+", line.split(";", 1)[0], re.IGNORECASE))
    print(f"Translated: {input_path} -> {output_path}")
    print(f"call sites: {call_count}; stack base: {choose_stack_base(parse_source(source), args.stack_base)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

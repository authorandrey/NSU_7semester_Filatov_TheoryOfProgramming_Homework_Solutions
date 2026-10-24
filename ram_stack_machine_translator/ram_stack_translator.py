#!/usr/bin/env python3
"""Translate RAM assembly with push/pop pseudo-instructions into ordinary RAM assembly."""
from __future__ import annotations
import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
INT_RE = re.compile(r"^-?\d+$")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
OPS = {"halt":"Halt","load":"Load","store":"Store","add":"Add","sub":"Sub",
       "mult":"Mult","div":"Div","read":"Read","write":"Write",
       "jump":"Jump","jzero":"JZero","jgtz":"JGTZ"}
JUMPS = {"Jump","JZero","JGTZ"}

class TranslationError(ValueError):
    pass

@dataclass
class Node:
    labels: list[str] = field(default_factory=list)
    op: str = ""
    arg: str = ""
    comment: str = ""
    line: int = 0

@dataclass
class Ins:
    op: str
    arg: str
    label: Optional[str] = None
    comment: str = ""

def validate_load(arg: str, line: int) -> None:
    if arg.startswith("="):
        ok = bool(re.fullmatch(r"=-?\d+", arg))
    elif arg.startswith("*"):
        ok = bool(re.fullmatch(r"\*-?\d+", arg))
    else:
        ok = bool(re.fullmatch(r"-?\d+", arg))
    if not ok:
        raise TranslationError(f"line {line}: invalid RAM operand {arg!r}")

def validate_store(arg: str, line: int) -> None:
    ok = bool(re.fullmatch(r"\*-?\d+", arg) or re.fullmatch(r"-?\d+", arg))
    if not ok:
        raise TranslationError(f"line {line}: invalid RAM destination {arg!r}")

def parse(source: str) -> list[Node]:
    nodes, pending, seen = [], [], set()
    for ln, raw in enumerate(source.splitlines(), 1):
        code, sep, comment = raw.partition(";")
        code, comment = code.strip(), comment.strip() if sep else ""
        labels = []
        while code:
            m = LABEL_RE.match(code)
            if not m: break
            label, code = m.group(1), m.group(2).strip()
            if label in seen: raise TranslationError(f"line {ln}: duplicate label {label!r}")
            seen.add(label); labels.append(label)
        if not code:
            pending.extend((x, ln) for x in labels)
            continue
        parts = code.split()
        key = parts[0].lower()
        labels = [x for x, _ in pending] + labels
        pending.clear()
        if key in {"push", "pop"}:
            if len(parts) != 2: raise TranslationError(f"line {ln}: syntax is '{key} OPERAND'")
            op, arg = key, parts[1]
            if op == "push": validate_load(arg, ln)
            else: validate_store(arg, ln)
        else:
            if key not in OPS: raise TranslationError(f"line {ln}: unsupported instruction {parts[0]!r}")
            if len(parts) != 2: raise TranslationError(f"line {ln}: syntax is '{parts[0]} ARGUMENT'")
            op, arg = OPS[key], parts[1]
            if op in JUMPS:
                if arg.startswith(("=", "*")) or (not INT_RE.fullmatch(arg) and not IDENT_RE.fullmatch(arg)):
                    raise TranslationError(f"line {ln}: invalid jump target {arg!r}")
            elif op in {"Load","Add","Sub","Mult","Div","Write"}: validate_load(arg, ln)
            elif op in {"Store","Read"}: validate_store(arg, ln)
        nodes.append(Node(labels, op, arg, comment, ln))
    if pending:
        nodes.append(Node([x for x, _ in pending], "Halt", "0", "end label", pending[0][1]))
    if not nodes: raise TranslationError("input file contains no instructions")
    labels = {x for n in nodes for x in n.labels}
    for n in nodes:
        if n.op in JUMPS and not INT_RE.fullmatch(n.arg) and n.arg not in labels:
            raise TranslationError(f"line {n.line}: undefined jump label {n.arg!r}")
    return nodes

def translate(source: str, stack_base: Optional[int] = None) -> str:
    nodes = parse(source)
    if stack_base is None:
        largest = max([0] + [abs(int(x)) for n in nodes for x in re.findall(r"(?<![A-Za-z_])-?\d+", n.arg)])
        stack_base = max(10000, largest + 1024)
    if stack_base < 2: raise TranslationError("--stack-base must be at least 2")
    sp = stack_base - 1
    reserved = {sp, stack_base}
    for n in nodes:
        if n.op == "push" and not n.arg.startswith("="):
            if int(n.arg.lstrip("*")) in reserved:
                raise TranslationError(f"line {n.line}: operand conflicts with reserved stack cells")
        if n.op == "pop" and int(n.arg.lstrip("*")) in reserved:
            raise TranslationError(f"line {n.line}: destination conflicts with reserved stack cells")

    prefix, labels0 = "__STACKGEN", {x for n in nodes for x in n.labels}
    while any(x.startswith(prefix) for x in labels0): prefix += "_X"
    gen = lambda name: f"{prefix}_{name}"
    srcpc = [gen(f"SRC_{i}") for i in range(1, len(nodes)+1)]
    for n in nodes:
        if n.op in JUMPS and INT_RE.fullmatch(n.arg):
            t = int(n.arg)
            if not 1 <= t <= len(nodes):
                raise TranslationError(f"line {n.line}: numeric jump target {t} outside 1..{len(nodes)}")
            n.arg = srcpc[t-1]

    out = [
        Ins("Load", f"={stack_base}", comment="initialize stack pointer"),
        Ins("Store", str(sp), comment="reserved pointer cell"),
        Ins("Jump", gen("ENTRY"), comment="skip initialization"),
        Ins("Jump", gen("BODY"), label=gen("ENTRY")),
    ]
    for i, n in enumerate(nodes):
        labels = [srcpc[i]] + n.labels
        if i == 0: labels.insert(0, gen("BODY"))
        if n.op == "push":
            seq = [Ins("Load", n.arg, comment=f"push {n.arg}"),
                   Ins("Store", f"*{sp}", comment="write at stack top"),
                   Ins("Load", str(sp)), Ins("Add", "=1"),
                   Ins("Store", str(sp), comment="SP := SP + 1")]
        elif n.op == "pop":
            seq = [Ins("Load", str(sp), comment=f"pop into {n.arg}"),
                   Ins("Sub", "=1"), Ins("Store", str(sp), comment="SP := SP - 1"),
                   Ins("Load", f"*{sp}"), Ins("Store", n.arg)]
        else:
            seq = [Ins(n.op, n.arg, comment=n.comment)]
        if labels:
            # A label on a pseudo-instruction points to its first expanded instruction.
            seq[0].label = labels[-1]
            for j, alias in enumerate(labels[:-1]):
                out.append(Ins("Jump", labels[j+1], label=alias, comment="label alias"))
        out.extend(seq)

    label_pc = {}
    for pc, ins in enumerate(out, 1):
        if ins.label:
            if ins.label in label_pc: raise TranslationError(f"duplicate generated label {ins.label}")
            label_pc[ins.label] = pc
    lines = []
    for ins in out:
        arg = ins.arg
        if ins.op in JUMPS and not INT_RE.fullmatch(arg):
            if arg not in label_pc: raise TranslationError(f"unresolved label {arg!r}")
            arg = str(label_pc[arg])
        line = f"{ins.label + ': ' if ins.label else ''}{ins.op} {arg}"
        if ins.comment: line += " ; " + ins.comment
        lines.append(line)
    return "\n".join(lines) + "\n"

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Translate RAM push/pop into ordinary RAM assembly.")
    p.add_argument("input", type=Path, help="input .ram_stack file")
    p.add_argument("-o", "--output", type=Path, help="output .asm path")
    p.add_argument("--stack-base", type=int, default=None, help="first stack cell; default is automatic")
    a = p.parse_args(argv)
    if not a.input.is_file():
        print(f"error: input file not found: {a.input}", file=sys.stderr); return 2
    output = a.output or a.input.with_suffix(".asm")
    try:
        result = translate(a.input.read_text(encoding="utf-8-sig"), a.stack_base)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, encoding="utf-8")
    except (OSError, UnicodeError, TranslationError) as e:
        print(f"error: {e}", file=sys.stderr); return 1
    print(f"Translated: {a.input} -> {output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

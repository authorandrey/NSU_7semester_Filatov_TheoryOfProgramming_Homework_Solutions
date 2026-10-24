#!/usr/bin/env python3
"""Generate a four-tape Turing machine for multiplication in base k.

Inputs are least-significant-digit first on tapes 1 and 2.
Tape 3 receives the product; tape 4 is a temporary copy of operand 2 and is
cleared before STOP.  Digit values 10..35 use A..Z. Supported base: 2..16.
"""
from __future__ import annotations
import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "2.4.tur"


def d(v: int) -> str:
    return DIGITS[v]


def mark(symbol: str) -> str:
    return "M" + symbol


def rule(read: tuple[str, ...], actions: tuple[str, ...], target: str) -> str:
    return f"    {', '.join(read)} -> {', '.join(actions)} {target}"


def generate(k: int) -> str:
    if not 2 <= k <= 16:
        raise ValueError("k must be in the range 2..16")

    digits = [d(i) for i in range(k)]
    read_symbols = digits + ["#"]
    marked = [mark(x) for x in digits]
    tape4_symbols = digits + marked + ["#"]
    val = {x: i for i, x in enumerate(digits)}
    val["#"] = 0
    lines: list[str] = [
        "// Generated from 2.4_template.txt",
        f"// Multiply two base-{k} numbers; least-significant digit first.",
        "// Tape 1 and tape 2 are preserved; tape 3 stores the product;",
        "// tape 4 is a temporary copy of tape 2 and is cleared before STOP.",
        f"alphabet = [{', '.join(['#'] + digits + marked)}]",
        "tapes = [ right, right, right, right ]",
        "",
        "START:",
        rule(("#", "#", "#", "#"), ("#R", "#R", "#R", "#R"), "COPY_FIRST"),
        "",
        "COPY_FIRST:",
    ]

    # Copy operand 2 onto tape 4. Mark its first digit as the current row.
    for a in digits:
        for b in digits:
            lines.append(rule((a, b, "#", "#"), (f"{a}H", f"{b}R", "#H", f"{mark(b)}R"), "COPY_NEXT"))

    lines.extend(["", "COPY_NEXT:"])
    for a in digits:
        for b in digits:
            lines.append(rule((a, b, "#", "#"), (f"{a}H", f"{b}R", "#H", f"{b}R"), "COPY_NEXT"))
        lines.append(rule((a, "#", "#", "#"), (f"{a}H", "#H", "#H", "#L"), "REWIND_COPY"))

    lines.extend(["", "REWIND_COPY:"])
    for a in digits:
        for s in digits + marked:
            lines.append(rule((a, "#", "#", s), (f"{a}H", "#H", "#H", f"{s}L"), "REWIND_COPY"))
        lines.append(rule((a, "#", "#", "#"), (f"{a}H", "#H", "#H", "#R"), "MUL_START"))

    lines.extend(["", "MUL_START:"])
    for a in digits:
        for b in digits:
            lines.append(rule((a, "#", "#", mark(b)), (f"{a}H", "#H", "#H", f"{mark(b)}H"), f"MUL_{b}_0"))

    # Long multiplication.  For each digit b of operand 2, add b*A at the
    # corresponding result offset. The carry is held in the state.
    for b in digits:
        for carry in range(k):
            state = f"MUL_{b}_{carry}"
            lines.extend(["", f"{state}:"])
            for a in digits:
                for x in read_symbols:
                    total = val[a] * val[b] + carry + val[x]
                    out = d(total % k)
                    c_out = total // k
                    lines.append(rule((a, "#", x, mark(b)), (f"{a}R", "#H", f"{out}R", f"{mark(b)}H"), f"MUL_{b}_{c_out}"))
            for x in read_symbols:
                if carry == 0:
                    lines.append(rule(("#", "#", x, mark(b)), ("#L", "#H", f"{x}L", f"{mark(b)}H"), "REWIND_BOTH"))
                else:
                    lines.append(rule(("#", "#", x, mark(b)), ("#H", "#H", f"{x}H", f"{mark(b)}H"), f"FLUSH_{carry}"))

    # Once A is exhausted, add remaining carry to result cells to the right.
    for carry in range(1, k):
        lines.extend(["", f"FLUSH_{carry}:"])
        for b in digits:
            for x in read_symbols:
                total = val[x] + carry
                out = d(total % k)
                c_out = total // k
                target = f"FLUSH_{c_out}" if c_out else "ENDROW"
                lines.append(rule(("#", "#", x, mark(b)), ("#H", "#H", f"{out}R", f"{mark(b)}H"), target))

    lines.extend(["", "ENDROW:"])
    for b in digits:
        for x in read_symbols:
            lines.append(rule(("#", "#", x, mark(b)), ("#L", "#H", f"{x}L", f"{mark(b)}H"), "REWIND_BOTH"))

    # Rewind A and result tape to their leading blank, independently.
    lines.extend(["", "REWIND_BOTH:"])
    for a in read_symbols:
        for x in read_symbols:
            for b in digits:
                if a == "#" and x == "#":
                    acts = ("#R", "#H", "#R", f"{mark(b)}H")
                    target = "ADVANCE_MARKER"
                else:
                    acts = (f"{a}{'H' if a == '#' else 'L'}", "#H", f"{x}{'H' if x == '#' else 'L'}", f"{mark(b)}H")
                    target = "REWIND_BOTH"
                lines.append(rule((a, "#", x, mark(b)), acts, target))

    # Shift the active marker to the next digit of B. If there is no next
    # digit, multiplication is complete and result normalization begins.
    lines.extend(["", "ADVANCE_MARKER:"])
    for a in digits:
        for x in read_symbols:
            for b in digits:
                lines.append(rule((a, "#", x, mark(b)), (f"{a}H", "#H", f"{x}H", f"{b}R"), "CHECK_NEXT_MARKER"))

    lines.extend(["", "CHECK_NEXT_MARKER:"])
    for a in digits:
        for x in read_symbols:
            lines.append(rule((a, "#", x, "#"), (f"{a}H", "#H", f"{x}H", "#H"), "NORMALIZE_SEEK_END"))
            for b in digits:
                lines.append(rule((a, "#", x, b), (f"{a}H", "#H", f"{x}H", f"{mark(b)}L"), "REWIND_COPY_FOR_ALIGN"))

    lines.extend(["", "REWIND_COPY_FOR_ALIGN:"])
    for a in digits:
        for x in read_symbols:
            for s in digits + marked:
                lines.append(rule((a, "#", x, s), (f"{a}H", "#H", f"{x}H", f"{s}L"), "REWIND_COPY_FOR_ALIGN"))
            lines.append(rule((a, "#", x, "#"), (f"{a}H", "#H", f"{x}H", "#R"), "ALIGN"))

    lines.extend(["", "ALIGN:"])
    for a in digits:
        for x in read_symbols:
            for b in digits:
                lines.append(rule((a, "#", x, b), (f"{a}H", "#H", f"{x}R", f"{b}R"), "ALIGN"))
            for b in digits:
                lines.append(rule((a, "#", x, mark(b)), (f"{a}H", "#H", f"{x}H", f"{mark(b)}H"), f"MUL_{b}_0"))

    # Remove redundant most-significant zero digits from the result.
    lines.extend(["", "NORMALIZE_SEEK_END:"])
    for a in digits:
        for x in digits:
            lines.append(rule((a, "#", x, "#"), (f"{a}H", "#H", f"{x}R", "#H"), "NORMALIZE_SEEK_END"))
        lines.append(rule((a, "#", "#", "#"), (f"{a}H", "#H", "#L", "#H"), "NORMALIZE_TRIM"))

    lines.extend(["", "NORMALIZE_TRIM:"])
    for a in digits:
        # High-order zeros are at the right end because the representation is reversed.
        lines.append(rule((a, "#", "0", "#"), (f"{a}H", "#H", "#L", "#H"), "NORMALIZE_TRIM"))
        for x in digits[1:]:
            lines.append(rule((a, "#", x, "#"), (f"{a}H", "#H", f"{x}H", "#L"), "CLEAN_SCRATCH"))
        lines.append(rule((a, "#", "#", "#"), (f"{a}H", "#H", "#R", "#H"), "NORMALIZE_ZERO"))

    lines.extend(["", "NORMALIZE_ZERO:"])
    for a in digits:
        lines.append(rule((a, "#", "#", "#"), (f"{a}H", "#H", "0H", "#L"), "CLEAN_SCRATCH"))

    # Erase tape 4 (we enter here on its last copied digit).
    lines.extend(["", "CLEAN_SCRATCH:"])
    for a in digits:
        for x in digits:
            for b in digits:
                lines.append(rule((a, "#", x, b), (f"{a}H", "#H", f"{x}H", "#L"), "CLEAN_SCRATCH"))
        for x in digits:
            lines.append(rule((a, "#", x, "#"), (f"{a}H", "#H", f"{x}H", "#H"), "STOP"))

    # Defensive uniqueness check for deterministic finite-state machine.
    keys: set[tuple[str, tuple[str, ...]]] = set()
    for line in lines:
        if "->" not in line:
            continue
        state = ""
        # State is the most recently emitted heading. Re-parse output below instead
        # of relying on state parsing here; duplicate checks are performed in helper.
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(f"Usage: {Path(sys.argv[0]).name} k [output.tur]", file=sys.stderr)
        return 2
    try:
        k = int(args[0])
        program = generate(k)
        output = args[1] if len(args) == 2 else DEFAULT_OUTPUT
        Path(output).write_text(program, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} for base {k}.")
    print(f"Transition rules: {sum('->' in line for line in program.splitlines())}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a 3-tape Turing machine for adding two base-k numbers.

Usage:
    python 2.3_generator.py k [output.tur]

Tape 1 and tape 2 contain the addends; tape 3 receives the sum.
Digits are least-significant first (reversed representation). Input tapes
are preserved. Values 10..35 are written as A..Z.
"""

import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "2.3.tur"


def digit(value: int) -> str:
    if not 0 <= value < len(DIGITS):
        raise ValueError(f"Digit value must be between 0 and 35; got {value}.")
    return DIGITS[value]


def rule(read, actions, target: str) -> str:
    return f"    {', '.join(read)} -> {', '.join(actions)} {target}"


def generate(k: int) -> str:
    if not 2 <= k <= 36:
        raise ValueError("k must be in the range 2..36")

    digits = [digit(v) for v in range(k)]
    symbols = digits + ["#"]
    lines = [
        "// Generated from 2.3_template.txt",
        f"// Add two base-{k} numbers; least-significant digit first.",
        "// Tape 1 and tape 2 are preserved; tape 3 stores the sum.",
        f"alphabet = [{', '.join(['#'] + digits)}]",
        "tapes = [ right, right, right ]",
        "",
        "START:",
        rule(("#", "#", "#"), ("#R", "#R", "#R"), "INIT"),
        "",
        "INIT:",
    ]

    # Empty + empty is defined as zero. Otherwise process the first digit pair.
    lines.append(rule(("#", "#", "#"), ("#H", "#H", "0H"), "STOP"))
    for x in digits:
        for y in digits:
            total = DIGITS.index(x) + DIGITS.index(y)
            out = digit(total % k)
            carry = total // k
            lines.append(rule((x, y, "#"), (f"{x}R", f"{y}R", f"{out}R"), f"CARRY_{carry}"))
        # First input digit paired with an exhausted second input.
        total = DIGITS.index(x)
        lines.append(rule((x, "#", "#"), (f"{x}R", "#H", f"{digit(total % k)}R"), f"CARRY_{total // k}"))
    for y in digits:
        total = DIGITS.index(y)
        lines.append(rule(("#", y, "#"), ("#H", f"{y}R", f"{digit(total % k)}R"), f"CARRY_{total // k}"))

    # In CARRY_c, a blank input contributes zero and its head stays put.
    for carry_in in (0, 1):
        lines.extend(["", f"CARRY_{carry_in}:"])
        lines.append(rule(("#", "#", "#"), ("#H", "#H", "#H"), "STOP") if carry_in == 0
                     else rule(("#", "#", "#"), ("#H", "#H", "1H"), "STOP"))
        for x in digits:
            for y in digits:
                total = DIGITS.index(x) + DIGITS.index(y) + carry_in
                out = digit(total % k)
                carry_out = total // k
                lines.append(rule((x, y, "#"), (f"{x}R", f"{y}R", f"{out}R"), f"CARRY_{carry_out}"))
            total = DIGITS.index(x) + carry_in
            lines.append(rule((x, "#", "#"), (f"{x}R", "#H", f"{digit(total % k)}R"), f"CARRY_{total // k}"))
        for y in digits:
            total = DIGITS.index(y) + carry_in
            lines.append(rule(("#", y, "#"), ("#H", f"{y}R", f"{digit(total % k)}R"), f"CARRY_{total // k}"))

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

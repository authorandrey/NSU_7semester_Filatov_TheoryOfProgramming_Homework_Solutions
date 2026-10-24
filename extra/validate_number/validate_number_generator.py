#!/usr/bin/env python3
"""Generate a one-tape TM that validates canonical base-m numerals.

Usage:
    python validate_number_generator.py m left|right
    python validate_number_generator.py m left|right output.tur

Only the blank marker and digits valid for base m are declared in alphabet.
Any other symbol has no transition, so the emulator rejects it automatically.
"""
from __future__ import annotations

import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "validate_number.tur"


def rule(read: str, write: str, move: str, target: str) -> str:
    return f"\t{read} -> {write}{move} {target}"


def generate(m: int, orientation: str) -> str:
    if not 2 <= m <= 36:
        raise ValueError("m must be in the range 2..36")
    if orientation not in {"left", "right"}:
        raise ValueError("orientation must be 'left' or 'right'")

    digits = list(DIGITS[:m])
    nonzero_digits = digits[1:]
    lines = [
        "// Generated from validate_number_template.txt",
        f"// Base m={m}; LSB {orientation}.",
        "// Canonical representation: no leading zeroes, except the numeral 0.",
        f"alphabet = [{', '.join(['#'] + digits)}]",
        "tapes = [ right ]",
        "",
        "START:",
    ]

    if orientation == "right":
        # Most-significant digit is the first symbol.
        lines.append(rule("#", "#", "R", "CHECK_FIRST"))
        lines.extend(["", "CHECK_FIRST:"])
        lines.append(rule("#", "#", "H", "ERROR"))  # empty input
        lines.append(rule("0", "0", "R", "CHECK_ZERO_FIRST"))
        for d in nonzero_digits:
            lines.append(rule(d, d, "R", "SCAN"))

        lines.extend(["", "CHECK_ZERO_FIRST:"])
        lines.append(rule("#", "#", "H", "STOP"))  # exactly "0"
        for d in digits:
            lines.append(rule(d, d, "H", "ERROR"))  # leading zero

        lines.extend(["", "SCAN:"])
        for d in digits:
            lines.append(rule(d, d, "R", "SCAN"))
        lines.append(rule("#", "#", "H", "STOP"))

    else:
        # Least-significant digit is the first symbol; inspect the final digit.
        lines.append(rule("#", "#", "R", "SCAN"))
        lines.extend(["", "SCAN:"])
        for d in digits:
            lines.append(rule(d, d, "R", "SCAN"))
        lines.append(rule("#", "#", "L", "CHECK_MSD"))

        lines.extend(["", "CHECK_MSD:"])
        lines.append(rule("#", "#", "H", "ERROR"))  # empty input
        lines.append(rule("0", "0", "L", "CHECK_SINGLE_ZERO"))
        for d in nonzero_digits:
            lines.append(rule(d, d, "H", "STOP"))

        lines.extend(["", "CHECK_SINGLE_ZERO:"])
        lines.append(rule("#", "#", "H", "STOP"))  # exactly "0"
        for d in digits:
            lines.append(rule(d, d, "H", "ERROR"))  # high-order zero in longer numeral

    # Deliberately do not add transitions for symbols outside the base-m alphabet.
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (2, 3):
        print(
            f"Usage: {Path(sys.argv[0]).name} m left|right [output.tur]",
            file=sys.stderr,
        )
        return 2
    try:
        m = int(args[0])
        orientation = args[1].lower()
        output = Path(args[2] if len(args) == 3 else DEFAULT_OUTPUT)
        program = generate(m, orientation)
        output.write_text(program, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} (base {m}, LSB {orientation}).")
    print(f"Transition rules: {sum('->' in line for line in program.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

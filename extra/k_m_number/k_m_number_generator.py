#!/usr/bin/env python3
"""Generate a 3-tape Turing machine converting a base-k number to base m.

Usage:
    python k_m_number_generator.py k m
    python k_m_number_generator.py k m output.tur

Input is on tape 1, least significant digit first. Tape 1 is preserved,
 tape 2 is cleared before STOP, and tape 3 receives the result LSF-first.
Digit values 10..35 are represented by A..Z.
"""

import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "k_m_number.tur"


def digit(value: int) -> str:
    """Map a digit value 0..35 to the one-symbol alphabet representation."""
    if not 0 <= value < len(DIGITS):
        raise ValueError(f"Digit value must be between 0 and 35; got {value}.")
    return DIGITS[value]


def rule(read, actions, target: str) -> str:
    """Format a multi-tape rule exactly as required by the emulator."""
    return f"\t{', '.join(read)} -> {', '.join(actions)} {target}"


def generate_mt(k: int, m: int) -> str:
    """Return a complete .tur program for converting a base-k number to base m."""
    if not 2 <= k <= 36:
        raise ValueError("k must be in the range 2..36")
    if not 2 <= m <= 36:
        raise ValueError("m must be in the range 2..36")

    input_digits = [digit(v) for v in range(k)]
    output_digits = [digit(v) for v in range(m)]
    alphabet_digits = [digit(v) for v in range(max(k, m))]
    lines = [
        "// Generated from k_m_number_template.txt",
        "// Input and output are written least-significant digit first.",
        f"// Conversion: base {k} -> base {m}.",
        f"alphabet = [{', '.join(['#'] + alphabet_digits)}]",
        "tapes = [ right, right, right ]",
        "",
        "START:",
        rule(("#", "#", "#"), ("#R", "#R", "#R"), "INIT"),
        "",
        "INIT:",
    ]

    # First input digit: initialize the result to 0; for empty input produce 0.
    for d in input_digits:
        lines.append(rule((d, "#", "#"), (f"{d}H", "#H", "0H"), "COPY_FIRST"))
    lines.append(rule(("#", "#", "#"), ("#H", "#H", "0H"), "STOP"))
    lines.extend(["", "COPY_FIRST:"])

    for d in input_digits:
        lines.append(rule((d, "#", "0"), (f"{d}R", f"{d}R", "0H"), "COPY"))
    lines.extend(["", "COPY:"])
    for d in input_digits:
        lines.append(rule((d, "#", "0"), (f"{d}R", f"{d}R", "0H"), "COPY"))
    lines.append(rule(("#", "#", "0"), ("#H", "#L", "0H"), "CONVERT"))
    lines.extend(["", "CONVERT:"])

    # Process the first output digit for the currently selected source digit d:
    # value = k*x + d. Output stores digits least-significant first.
    for d_value, d in enumerate(input_digits):
        for x_value, x in enumerate(output_digits):
            value = k * x_value + d_value
            out = digit(value % m)
            carry = value // m
            lines.append(rule(("#", d, x), ("#H", f"{d}H", f"{out}R"), f"CARRY_{carry}_SRC_{d_value}"))

    # No more source digits: return to the output's left boundary for cleanup.
    for x in output_digits:
        lines.append(rule(("#", "#", x), ("#H", "#H", f"{x}L"), "CLEAN_START"))

    # State holds carry c and current source digit d.
    for c in range(k):
        for d_value, d in enumerate(input_digits):
            lines.extend(["", f"CARRY_{c}_SRC_{d_value}:"])
            for x_value, x in enumerate(output_digits):
                value = k * x_value + c
                out = digit(value % m)
                next_carry = value // m
                lines.append(rule(("#", d, x), ("#H", f"{d}H", f"{out}R"), f"CARRY_{next_carry}_SRC_{d_value}"))

            if c == 0:
                lines.append(rule(("#", d, "#"), ("#H", f"{d}H", "#L"), "REWIND"))
            else:
                out = digit(c % m)
                remaining = c // m
                if remaining == 0:
                    action = f"{out}L"
                    target = "REWIND"
                else:
                    action = f"{out}R"
                    target = f"FLUSH_{remaining}"
                lines.append(rule(("#", d, "#"), ("#H", f"{d}H", action), target))

    # If a carry is at least m, emit its remaining base-m digits one at a time.
    for q in range(1, k):
        lines.extend(["", f"FLUSH_{q}:"])
        out = digit(q % m)
        remaining = q // m
        if remaining == 0:
            action = f"{out}L"
            target = "REWIND"
        else:
            action = f"{out}R"
            target = f"FLUSH_{remaining}"
        for d in input_digits:
            lines.append(rule(("#", d, "#"), ("#H", f"{d}H", action), target))

    lines.extend(["", "REWIND:"])
    for d in input_digits:
        for x in output_digits:
            lines.append(rule(("#", d, x), ("#H", f"{d}H", f"{x}L"), "REWIND"))
        lines.append(rule(("#", d, "#"), ("#H", f"{d}L", "#R"), "CONVERT"))

    lines.extend(["", "CLEAN_START:"])
    lines.append(rule(("#", "#", "#"), ("#H", "#R", "#H"), "CLEAN_2"))
    lines.extend(["", "CLEAN_2:"])
    for d in input_digits:
        lines.append(rule(("#", d, "#"), ("#H", "#R", "#H"), "CLEAN_2"))
    lines.append(rule(("#", "#", "#"), ("#H", "#H", "#H"), "STOP"))
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 0:
        try:
            k = int(input("Input base k: "))
            m = int(input("Input base m: "))
        except ValueError:
            print("Bases must be integers.", file=sys.stderr)
            return 2
        filename = input(f"Output filename [{DEFAULT_OUTPUT}]: ").strip() or DEFAULT_OUTPUT
    elif len(args) in (2, 3):
        try:
            k = int(args[0])
            m = int(args[1])
        except ValueError:
            print("Bases must be integers.", file=sys.stderr)
            return 2
        filename = args[2] if len(args) == 3 else DEFAULT_OUTPUT
    else:
        print(f"Usage: {Path(sys.argv[0]).name} k m [output.tur]", file=sys.stderr)
        return 2

    try:
        program = generate_mt(k, m)
        Path(filename).write_text(program, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {filename} for base {k} -> base {m}.")
    print(f"Transition rules: {sum('->' in line for line in program.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

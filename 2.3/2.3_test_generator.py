#!/usr/bin/env python3
"""Generate tests for the 3-tape base-k addition machine.

Usage:
    python 2.3_test_generator.py k [output.test]

Tape contents use #word# notation; digits are least-significant first.
The multi-tape test runner separates tape contents with vertical bars.
"""

import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "2.3.test"


def encode_lsf(n: int, base: int) -> str:
    if n == 0:
        return "0"
    out = []
    while n:
        out.append(DIGITS[n % base])
        n //= base
    return "".join(out)


def tape(word: str) -> str:
    return f"#{word}#" if word else "#"


def test_line(name: str, a: str, b: str, c: str) -> str:
    return f"{name:<20}: {tape(a)}|{tape(b)}|{tape('')} -> {tape(a)}|{tape(b)}|{tape(c)}"


def generate_tests(k: int) -> str:
    if not 2 <= k <= 36:
        raise ValueError("k must be in the range 2..36")
    cases = [
        ("empty_plus_empty", 0, 0, True),
        ("zero_plus_zero", 0, 0, False),
        ("zero_plus_one", 0, 1, False),
        ("one_plus_one", 1, 1, False),
        ("carry_at_last_digit", k - 1, 1, False),
        ("two_digit_sum", k + 1, k + 2, False),
        ("different_lengths", 1, k * k + k + 1, False),
        ("long_carry_chain", k**4 - 1, 1, False),
        ("same_number", k**3 + k + 2, k**3 + k + 2, False),
        ("large_sum", k**5 + 2 * k**3 + k - 1, k**4 + 3 * k**2 + 2, False),
    ]
    lines = [f"// Base {k}; inputs and output use least-significant digit first."]
    for name, a_value, b_value, empty in cases:
        if empty:
            a, b, c = "", "", "0"
        else:
            a = encode_lsf(a_value, k)
            b = encode_lsf(b_value, k)
            c = encode_lsf(a_value + b_value, k)
        lines.append(test_line(name, a, b, c))

    # A compact sweep over pairs of one-digit values exercises every digit pair.
    for a_value in range(k):
        for b_value in range(k):
            a = encode_lsf(a_value, k)
            b = encode_lsf(b_value, k)
            c = encode_lsf(a_value + b_value, k)
            lines.append(test_line(f"digit_{a_value}_{b_value}", a, b, c))
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(f"Usage: {Path(sys.argv[0]).name} k [output.test]", file=sys.stderr)
        return 2
    try:
        k = int(args[0])
        contents = generate_tests(k)
        output = args[1] if len(args) == 2 else DEFAULT_OUTPUT
        Path(output).write_text(contents, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} for base {k}.")
    print(f"Tests: {sum(line.startswith('test_') or ':' in line and not line.startswith('//') for line in contents.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

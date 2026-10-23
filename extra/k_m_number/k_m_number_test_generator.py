#!/usr/bin/env python3
"""Generate emulator tests for conversion from base k to base m.

Usage:
    python k_m_number_test_generator.py k m
    python k_m_number_test_generator.py k m output.test

The generated tests use the repository emulator format. Tape contents are
separated by '|'. Input and output numbers are stored least-significant digit
first. Tape 1 is expected to remain unchanged and tape 2 to be cleared.
Digits 10..35 are represented by A..Z.
"""

from __future__ import annotations

import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
    "twenty_one", "twenty_two", "twenty_three", "twenty_four", "twenty_five",
    "twenty_six", "twenty_seven", "twenty_eight", "twenty_nine", "thirty",
    "thirty_one", "thirty_two", "thirty_three", "thirty_four", "thirty_five",
)
DEFAULT_OUTPUT = "k_m_number.test"


def to_reversed_digits(number: int, base: int) -> str:
    """Encode a nonnegative integer in `base`, least-significant digit first."""
    if number < 0:
        raise ValueError("Only nonnegative integers are supported.")
    if number == 0:
        return "0"
    result = []
    while number:
        result.append(DIGITS[number % base])
        number //= base
    return "".join(result)


def tape_number(number: int, base: int) -> str:
    return f"#{to_reversed_digits(number, base)}#"


def make_test(name: str, input_number: int | None, k: int, m: int) -> str:
    # None represents an empty input word; the machine is expected to treat it as 0.
    tape1 = "#" if input_number is None else tape_number(input_number, k)
    value = 0 if input_number is None else input_number
    tape2 = "#"
    tape3 = tape_number(value, m)
    return f"{name:<29}: {tape1}|{tape2}|# -> {tape1}|{tape2}|{tape3}"


def generate_tests(k: int, m: int) -> str:
    if not 2 <= k <= 36:
        raise ValueError("k must be in the range 2..36")
    if not 2 <= m <= 36:
        raise ValueError("m must be in the range 2..36")

    cases: list[tuple[str, int | None]] = [("test_empty", None), ("test_zero", 0)]

    # Exercise every possible single input digit.
    for value in range(1, k):
        cases.append((f"test_digit_{NUMBER_WORDS[value]}", value))

    # Exercise carry propagation, changes in output length, and relationships
    # between the two bases.
    named_values = [
        ("test_k", k),
        ("test_k_plus_one", k + 1),
        ("test_k_squared_minus_one", k**2 - 1),
        ("test_k_squared", k**2),
        ("test_k_squared_plus_one", k**2 + 1),
        ("test_k_cubed_minus_one", k**3 - 1),
        ("test_k_cubed", k**3),
        ("test_k_cubed_plus_one", k**3 + 1),
        ("test_m_minus_one", m - 1),
        ("test_m", m),
        ("test_m_plus_one", m + 1),
        ("test_m_squared_minus_one", m**2 - 1),
        ("test_m_squared", m**2),
        ("test_m_squared_plus_one", m**2 + 1),
        ("test_m_cubed_minus_one", m**3 - 1),
        ("test_m_cubed", m**3),
        ("test_m_cubed_plus_one", m**3 + 1),
        ("test_k_times_m_minus_one", k * m - 1),
        ("test_k_times_m", k * m),
        ("test_k_times_m_plus_one", k * m + 1),
    ]
    cases.extend(named_values)

    lines = [
        f"// Automatically generated tests for conversion from base {k} to base {m}.",
        "// Tape format: tape1|tape2|tape3. Numbers are written least-significant digit first.",
        "// Expected: tape 1 unchanged, tape 2 cleared, converted number on tape 3.",
    ]
    lines.extend(make_test(name, number, k, m) for name, number in cases)
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (2, 3):
        print(
            f"Usage: {Path(sys.argv[0]).name} k m [output.test]",
            file=sys.stderr,
        )
        return 2
    try:
        k, m = int(args[0]), int(args[1])
        output = Path(args[2] if len(args) == 3 else DEFAULT_OUTPUT)
        content = generate_tests(k, m)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {output} for base {k} -> base {m}.")
    print(f"Tests: {sum(line.startswith('test_') for line in content.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

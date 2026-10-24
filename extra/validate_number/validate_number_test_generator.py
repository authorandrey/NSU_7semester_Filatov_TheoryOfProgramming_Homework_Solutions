#!/usr/bin/env python3
"""Generate tests for the canonical base-m numeral validator.

Usage:
    python validate_number_test_generator.py m left|right
    python validate_number_test_generator.py m left|right output.test

Test cases include symbols outside the declared alphabet: the TM should reach
ERROR automatically because the generated program has no transition for them.
"""
from __future__ import annotations

import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "validate_number.test"


def encode(number: int, base: int, orientation: str) -> str:
    """Return a canonical numeral with the requested least-significant side."""
    if number == 0:
        return "0"
    reversed_digits: list[str] = []
    while number:
        reversed_digits.append(DIGITS[number % base])
        number //= base
    lsf_first = "".join(reversed_digits)
    return lsf_first if orientation == "left" else lsf_first[::-1]


def make_test(name: str, raw: str, valid: bool) -> str:
    input_tape = f"#{raw}#" if raw else "#"
    expected = f"#{raw}#" if valid else "ERROR"
    return f"{name:<31}: {input_tape} -> {expected}"


def generate_tests(m: int, orientation: str) -> str:
    if not 2 <= m <= 36:
        raise ValueError("m must be in the range 2..36")
    if orientation not in {"left", "right"}:
        raise ValueError("orientation must be 'left' or 'right'")

    valid_cases: list[tuple[str, str]] = []
    seen_valid: set[str] = set()

    def add_valid(name: str, value: int) -> None:
        raw = encode(value, m, orientation)
        if raw not in seen_valid:
            valid_cases.append((name, raw))
            seen_valid.add(raw)

    add_valid("test_valid_zero", 0)
    for value in range(1, m):
        add_valid(f"test_digit_{DIGITS[value]}", value)
    for name, value in [
        ("test_value_one", 1),
        ("test_base", m),
        ("test_base_plus_one", m + 1),
        ("test_base_squared_minus_one", m * m - 1),
        ("test_base_squared", m * m),
        ("test_base_squared_plus_one", m * m + 1),
        ("test_base_cubed_minus_one", m**3 - 1),
        ("test_base_cubed", m**3),
        ("test_base_cubed_plus_one", m**3 + 1),
    ]:
        add_valid(name, value)

    invalid_cases: list[tuple[str, str]] = [("test_empty", "")]
    for value in range(m, 36):
        invalid_cases.append((f"test_invalid_digit_{DIGITS[value]}", DIGITS[value]))
    invalid_cases.extend([
        ("test_lowercase_letter", "a"),
        ("test_punctuation", "?"),
        ("test_invalid_suffix", "1a"),
        ("test_invalid_prefix", "a1"),
        ("test_invalid_symbol_after_digits", "1010a"),
        ("test_zero_zero", "00"),
        ("test_multiple_zeroes", "000"),
    ])
    if orientation == "right":
        invalid_cases.extend([
            ("test_leading_zero_one", "01"),
            ("test_leading_zero_base", "0" + encode(m, m, orientation)),
        ])
    else:
        invalid_cases.extend([
            ("test_trailing_zero_one", "10"),
            ("test_trailing_zero_base", encode(m, m, orientation) + "0"),
        ])

    dedup_invalid: list[tuple[str, str]] = []
    seen_invalid: set[str] = set()
    for name, raw in invalid_cases:
        if raw not in seen_invalid:
            dedup_invalid.append((name, raw))
            seen_invalid.add(raw)

    lines = [
        f"// Validate canonical base-{m} numerals; LSB {orientation}.",
        "// Valid input is left unchanged and halts in STOP; invalid input reaches ERROR.",
        "// The alphabet only contains # and base-m digits; other symbols have no transition.",
        "// Empty input is represented by '#'. Digits 10..35 are A..Z.",
    ]
    lines.extend(make_test(name, raw, True) for name, raw in valid_cases)
    lines.extend(make_test(name, raw, False) for name, raw in dedup_invalid)
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (2, 3):
        print(
            f"Usage: {Path(sys.argv[0]).name} m left|right [output.test]",
            file=sys.stderr,
        )
        return 2
    try:
        m = int(args[0])
        orientation = args[1].lower()
        output = Path(args[2] if len(args) == 3 else DEFAULT_OUTPUT)
        content = generate_tests(m, orientation)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    count = sum(line.startswith("test_") and ":" in line for line in content.splitlines())
    print(f"Generated {output}. Tests: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

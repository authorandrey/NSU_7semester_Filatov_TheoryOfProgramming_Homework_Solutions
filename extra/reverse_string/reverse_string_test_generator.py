#!/usr/bin/env python3
"""Generate tests for reverse_string_generator.py.

Usage:
    python reverse_string_test_generator.py abc
    python reverse_string_test_generator.py abc 4
    python reverse_string_test_generator.py abc 4 reverse_string.test

The optional max_length controls exhaustive word length. The default is the
largest length up to 4 that keeps the test suite at or below 5,000 cases.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

DEFAULT_OUTPUT = "reverse_string.test"
MAX_TESTS = 5000


def parse_alphabet(raw: str) -> list[str]:
    if "," in raw:
        symbols = [part.strip() for part in raw.split(",")]
    else:
        symbols = list(raw)
    if not symbols or any(symbol == "" for symbol in symbols):
        raise ValueError("alphabet must contain at least one symbol")
    for symbol in symbols:
        if len(symbol) != 1:
            raise ValueError("every alphabet symbol must be exactly one character")
        if symbol.isspace() or symbol in {"#", ",", ":", "|"}:
            raise ValueError("alphabet symbols cannot be whitespace, '#', ',', ':' or '|'")
    if len(set(symbols)) != len(symbols):
        raise ValueError("alphabet symbols must be distinct")
    return symbols


def default_max_length(alphabet_size: int) -> int:
    total = 1
    result = 0
    for length in range(1, 5):
        total += alphabet_size**length
        if total > MAX_TESTS:
            break
        result = length
    return max(1, result)


def encode_test_word(word: str) -> str:
    # The emulator's empty input convention is a single '#'.
    return "#" if word == "" else f"#{word}#"


def make_test(name: str, word: str) -> str:
    return f"{name:<27}: {encode_test_word(word)} -> {encode_test_word(word[::-1])}"


def generate(alphabet: list[str], max_length: int | None = None) -> str:
    if max_length is None:
        max_length = default_max_length(len(alphabet))
    if max_length < 0 or max_length > 8:
        raise ValueError("max_length must be in the range 0..8")
    count = sum(len(alphabet) ** length for length in range(max_length + 1))
    if count > MAX_TESTS:
        raise ValueError(
            f"this would generate {count} tests; choose max_length so the total is at most {MAX_TESTS}"
        )

    lines = [
        f"// Automatically generated reversal tests for alphabet {{{', '.join(alphabet)}}}.",
        "// Format: #word# -> #reverse(word)#; empty word is represented by '#'.",
    ]
    lines.append(make_test("test_empty", ""))
    serial = 0
    for length in range(1, max_length + 1):
        for chars in itertools.product(alphabet, repeat=length):
            word = "".join(chars)
            lines.append(make_test(f"test_len{length}_{serial:04d}", word))
            serial += 1
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2, 3):
        print(
            f"Usage: {Path(sys.argv[0]).name} alphabet [max_length] [output.test]",
            file=sys.stderr,
        )
        return 2
    try:
        alphabet = parse_alphabet(args[0])
        if len(args) >= 2:
            try:
                max_length = int(args[1])
            except ValueError as exc:
                raise ValueError("max_length must be an integer") from exc
        else:
            max_length = None
        output = Path(args[2] if len(args) == 3 else DEFAULT_OUTPUT)
        content = generate(alphabet, max_length)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} for alphabet {{{', '.join(alphabet)}}}.")
    print(f"Tests: {sum(line.startswith('test_') for line in content.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

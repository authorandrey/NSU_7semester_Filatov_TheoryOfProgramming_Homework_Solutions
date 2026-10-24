#!/usr/bin/env python3
"""Generate emulator tests for erase_prefix_before_match.

Usage:
    python erase_prefix_before_match_test_generator.py PATTERN
    python erase_prefix_before_match_test_generator.py PATTERN output.test

The pattern and input words use the fixed alphabet {a,b}. When a match exists,
the output is the word beginning at its leftmost occurrence; the prefix cells
are represented by extra '#' symbols. If no match exists, the whole tape is
blank and is represented by '#'.
"""

from __future__ import annotations

from itertools import product
import sys
from pathlib import Path

ALPHABET = "ab"
DEFAULT_OUTPUT = "erase_prefix_before_match.test"


def validate_pattern(pattern: str) -> None:
    if not pattern:
        raise ValueError("PATTERN must be a non-empty word over {a,b}")
    invalid = sorted(set(pattern) - set(ALPHABET))
    if invalid:
        raise ValueError(
            "PATTERN may contain only 'a' and 'b'; invalid symbols: "
            + ", ".join(repr(c) for c in invalid)
        )


def input_tape(word: str) -> str:
    return f"#{word}#" if word else "#"


def expected_tape(word: str, pattern: str) -> str:
    start = word.find(pattern)
    if start < 0:
        # The machine has replaced every input symbol by a blank.
        return "#"
    return "#" * (start + 1) + word[start:] + "#"


def generate_tests(pattern: str, max_exhaustive_length: int = 6) -> str:
    validate_pattern(pattern)
    if max_exhaustive_length < 0:
        raise ValueError("max_exhaustive_length must be non-negative")

    length = len(pattern)
    opposite_first = "b" if pattern[0] == "a" else "a"
    opposite_last = "b" if pattern[-1] == "a" else "a"
    cases: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(name: str, word: str) -> None:
        if word not in seen:
            seen.add(word)
            cases.append((name, word))

    # Focused boundary and overlap cases.
    add("test_empty", "")
    add("test_exact_match", pattern)
    add("test_prefix_before_match", opposite_first + pattern)
    add("test_match_with_suffix", pattern + opposite_last)
    add("test_prefix_match_suffix", opposite_first + pattern + opposite_last)
    add("test_two_matches", pattern + pattern)
    add("test_near_miss_at_end", pattern[:-1] + opposite_last)
    add("test_pattern_prefix_then_match", pattern[:-1] + pattern)
    add("test_all_a", "a" * max(1, length + 1))
    add("test_all_b", "b" * max(1, length + 1))
    add("test_alternating_ab", "ab" * ((length + 2) // 2))
    add("test_alternating_ba", "ba" * ((length + 2) // 2))

    # Exhaustive short inputs help exercise KMP fallback transitions.
    serial = 0
    for n in range(max_exhaustive_length + 1):
        for chars in product(ALPHABET, repeat=n):
            word = "".join(chars)
            if word not in seen:
                serial += 1
                add(f"test_short_{serial:03d}", word)

    width = max(len(name) for name, _ in cases)
    lines = [
        f"// Tests for erase_prefix_before_match, P={pattern!r} over {{a,b}}.",
        "// On match: erase the prefix before the leftmost occurrence; keep match and suffix.",
        "// On no match: erase the complete input. Empty tape is represented by '#'.",
    ]
    for name, word in cases:
        lines.append(
            f"{name:<{width}} : {input_tape(word)} -> {expected_tape(word, pattern)}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2, 3):
        print(
            f"Usage: {Path(sys.argv[0]).name} PATTERN [max_length] [output.test]",
            file=sys.stderr,
        )
        return 2

    pattern = args[0]
    try:
        if len(args) == 1:
            max_length = 6
            output = Path(DEFAULT_OUTPUT)
        elif len(args) == 2:
            # A numeric second argument means exhaustive input length; otherwise filename.
            try:
                max_length = int(args[1])
                output = Path(DEFAULT_OUTPUT)
            except ValueError:
                max_length = 6
                output = Path(args[1])
        else:
            max_length = int(args[1])
            output = Path(args[2])
        content = generate_tests(pattern, max_length)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    count = sum(bool(line.strip()) and not line.lstrip().startswith("//") for line in content.splitlines())
    print(f"Generated {output} for pattern {pattern!r}: {count} tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

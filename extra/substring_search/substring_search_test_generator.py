#!/usr/bin/env python3
"""Generate emulator tests for the fixed-substring search machine.

Usage:
    python substring_search_test_generator.py aababab
    python substring_search_test_generator.py aababab custom.test

The expected output matches the optimized task-1.7 convention: if found, the
prefix before the leftmost occurrence is erased, the occurrence and suffix are
kept; otherwise the complete input word is erased.
"""

from __future__ import annotations

from itertools import product
import sys
from pathlib import Path

DEFAULT_OUTPUT = "substring_search.test"
ALPHABET = "ab"


def validate_pattern(pattern: str) -> None:
    if not pattern:
        raise ValueError("pattern must be a non-empty word over {a,b}")
    if any(symbol not in ALPHABET for symbol in pattern):
        raise ValueError("pattern must contain only 'a' and 'b'")


def input_tape(word: str) -> str:
    return "#" if not word else f"#{word}#"


def expected_tape(word: str, pattern: str) -> str:
    start = word.find(pattern)
    if start < 0:
        # All cells of the input have been blanked; '#' is the default tape symbol.
        return "#"
    # The left boundary plus the erased prefix; the match and suffix remain.
    return "#" * (start + 1) + word[start:] + "#"


def generate_tests(pattern: str) -> str:
    validate_pattern(pattern)
    opposite_first = "b" if pattern[0] == "a" else "a"
    opposite_last = "b" if pattern[-1] == "a" else "a"
    length = len(pattern)

    cases: list[tuple[str, str]] = []
    seen_words: set[str] = set()

    def add(name: str, word: str) -> None:
        if word not in seen_words:
            seen_words.add(word)
            cases.append((name, word))

    # Named edge cases: empty input, exact match, match after a prefix and suffix.
    add("test_empty", "")
    add("test_exact", pattern)
    add("test_prefixed", opposite_first + pattern)
    add("test_suffixed", pattern + opposite_last)
    add("test_embedded", opposite_first + pattern + opposite_last)
    add("test_repeated", pattern + pattern)

    # Near misses, including a correct prefix followed by a wrong final symbol.
    if length > 1:
        add("test_prefix_short", pattern[:-1])
    add("test_last_mismatch", pattern[:-1] + opposite_last)
    add("test_first_mismatch", opposite_first + pattern[:-1])

    # Inputs likely to exercise fallback transitions in the prefix automaton.
    for name, word in (
        ("test_all_a", "a" * (length + 1)),
        ("test_all_b", "b" * (length + 1)),
        ("test_alternating_ab", "ab" * ((length + 2) // 2)),
        ("test_alternating_ba", "ba" * ((length + 2) // 2)),
        ("test_pattern_prefix_suffix", pattern[:-1] + pattern),
    ):
        add(name, word)

    # Exhaustively add short words to catch overlaps and mismatches.
    # Capped at length 6 to keep the test file small even for long patterns.
    exhaustive_length = min(length + 1, 6)
    serial = 0
    for n in range(exhaustive_length + 1):
        for chars in product(ALPHABET, repeat=n):
            word = "".join(chars)
            if word not in seen_words:
                serial += 1
                add(f"test_short_{serial:03d}", word)

    lines = [
        f"// Generated substring tests for P={pattern!r} over alphabet {{a,b}}.",
        "// If found: erase the prefix before the leftmost match; preserve match and suffix.",
        "// If absent: erase the whole word. A completely erased tape is represented by '#'.",
    ]
    width = max(len(name) for name, _ in cases)
    for name, word in cases:
        lines.append(
            f"{name:<{width}} : {input_tape(word)} -> {expected_tape(word, pattern)}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(
            f"Usage: {Path(sys.argv[0]).name} PATTERN [output.test]",
            file=sys.stderr,
        )
        return 2
    pattern = args[0]
    output = Path(args[1] if len(args) == 2 else DEFAULT_OUTPUT)
    try:
        content = generate_tests(pattern)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    count = sum(line.strip() and not line.lstrip().startswith("//") for line in content.splitlines())
    print(f"Generated {output} for pattern {pattern!r}: {count} tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate tests for the TM that checks whether an input word is a substring of db.

Usage:
    python db_substring_test_generator.py aababababaabbbababaaab
    python db_substring_test_generator.py aababababaabbbababaaab custom.test
"""
from __future__ import annotations
from itertools import product
import sys
from pathlib import Path

ALPHABET = "ab"
DEFAULT_OUTPUT = "db_substring.test"


def validate_db(db: str) -> None:
    if not db:
        raise ValueError("db must be a non-empty word over {a,b}")
    if any(ch not in ALPHABET for ch in db):
        raise ValueError("db must contain only 'a' and 'b'")


def all_substrings(db: str) -> set[str]:
    result = {""}
    for i in range(len(db)):
        for j in range(i + 1, len(db) + 1):
            result.add(db[i:j])
    return result


def tape(word: str) -> str:
    return "#" if not word else f"#{word}#"


def generate_tests(db: str) -> str:
    validate_db(db)
    substrings = all_substrings(db)
    cases: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def add(name: str, word: str) -> None:
        if word in seen:
            return
        seen.add(word)
        expected = "#" if word in substrings else "ERROR"
        cases.append((name, word, expected))

    add("test_empty", "")
    add("test_full_db", db)
    # Every distinct positive candidate is included.
    for i, word in enumerate(sorted((s for s in substrings if s), key=lambda s: (len(s), s)), 1):
        add(f"test_substring_{i:04d}", word)

    # All short candidates exercise both accepted and rejected transitions.
    exhaustive_length = min(len(db) + 1, 8)
    serial = 0
    for n in range(exhaustive_length + 1):
        for chars in product(ALPHABET, repeat=n):
            word = "".join(chars)
            if word not in seen and word not in substrings:
                serial += 1
                add(f"test_not_substring_{serial:04d}", word)

    # Explicit overlong and near-boundary candidates guarantee negative cases
    # even when db is long and all short words happen to occur in it.
    for name, word in (
        ("test_too_long_a", "a" * (len(db) + 1)),
        ("test_too_long_b", "b" * (len(db) + 1)),
        ("test_alternating_ab", ("ab" * ((len(db) + 2) // 2))[:len(db) + 1]),
        ("test_alternating_ba", ("ba" * ((len(db) + 2) // 2))[:len(db) + 1]),
    ):
        add(name, word)

    lines = [
        f"// Generated tests for checking whether a candidate is a substring of db={db}.",
        "// Accepted: STOP and the input word is erased (#). Rejected: ERROR.",
    ]
    width = max(len(name) for name, _, _ in cases)
    for name, word, expected in cases:
        lines.append(f"{name:<{width}} : {tape(word)} -> {expected}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(f"Usage: {Path(sys.argv[0]).name} DB [output.test]", file=sys.stderr)
        return 2
    db = args[0]
    output = Path(args[1] if len(args) == 2 else DEFAULT_OUTPUT)
    try:
        content = generate_tests(db)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    count = sum(line.strip() and not line.lstrip().startswith("//") for line in content.splitlines())
    print(f"Generated {output} for db={db!r}: {count} tests.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

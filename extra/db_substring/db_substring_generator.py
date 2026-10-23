#!/usr/bin/env python3
"""Generate a one-tape TM checking whether an input word is a substring of db.

Usage:
    python db_substring_generator.py aababababaabbbababaaab
    python db_substring_generator.py aababababaabbbababaaab custom.tur

On success, the candidate word is erased and the machine halts in STOP.
On failure, it halts in ERROR.
"""
from __future__ import annotations
import sys
from pathlib import Path

ALPHABET = "ab"
DEFAULT_OUTPUT = "db_substring.tur"


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


def state_name(word: str) -> str:
    return "PREFIX_EMPTY" if word == "" else "PREFIX_" + word.upper()


def generate_mt(db: str) -> str:
    validate_db(db)
    substrings = all_substrings(db)
    ordered = sorted(substrings, key=lambda w: (len(w), w))
    lines = [
        "alphabet = [#, a, b]",
        "tapes = [ right ]",
        "",
        f"// Fixed database string db = {db}",
        "// The input is accepted iff it is a substring of db.",
        "// Accepted input symbols are erased as they are read; invalid extensions go to ERROR.",
        "",
        "START:",
        "    # -> #R PREFIX_EMPTY",
        "",
    ]
    for word in ordered:
        lines.append(f"{state_name(word)}:")
        lines.append("    # -> #H STOP")
        for ch in ALPHABET:
            extended = word + ch
            if extended in substrings:
                lines.append(f"    {ch} -> #R {state_name(extended)}")
            else:
                lines.append(f"    {ch} -> {ch}H ERROR")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(f"Usage: {Path(sys.argv[0]).name} DB [output.tur]", file=sys.stderr)
        return 2
    db = args[0]
    output = Path(args[1] if len(args) == 2 else DEFAULT_OUTPUT)
    try:
        output.write_text(generate_mt(db), encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} for db={db!r}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

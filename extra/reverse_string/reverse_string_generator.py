#!/usr/bin/env python3
"""Generate a one-tape Turing machine that reverses a string in place.

Usage:
    python reverse_string_generator.py abc
    python reverse_string_generator.py a,b,c reverse_string.tur

The input is #word# and the result is #reverse(word)#. The empty input is
represented by '#'. Alphabet symbols are single characters; '#' is reserved
for the tape blank/boundary marker. During execution, L0..L{n-1} and
R0..R{n-1} mark characters whose positions have already been processed.
"""
from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_OUTPUT = "reverse_string.tur"


def parse_alphabet(raw: str) -> list[str]:
    """Accept either a compact alphabet like 'abc' or comma-separated symbols."""
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


def rule(read: str, write: str, move: str, target: str) -> str:
    return f"\t{read} -> {write}{move} {target}"


def generate(alphabet: list[str]) -> str:
    """Return a complete one-tape TM program for reversing strings."""
    if not alphabet:
        raise ValueError("alphabet must not be empty")
    n = len(alphabet)
    left_mark = [f"L{i}" for i in range(n)]
    right_mark = [f"R{i}" for i in range(n)]

    all_symbols = ["#"] + alphabet + left_mark + right_mark
    lines = [
        "// Generated from reverse_string_template.txt",
        "// Reverse a word over the supplied finite alphabet.",
        f"// Input alphabet: {{{', '.join(alphabet)}}}",
        "// Input/output format: #word# -> #reverse(word)#; empty input is '#'.",
        f"alphabet = [{', '.join(all_symbols)}]",
        "tapes = [ right ]",
        "",
        "START:",
        rule("#", "#", "R", "FIND_LEFT"),
        "",
        "FIND_LEFT:",
    ]

    # Skip processed left-hand characters; mark the leftmost unprocessed one.
    for i, symbol in enumerate(alphabet):
        lines.append(rule(left_mark[i], left_mark[i], "R", "FIND_LEFT"))
    for i, symbol in enumerate(alphabet):
        lines.append(rule(symbol, left_mark[i], "R", f"GO_RIGHT_{i}"))
    for mark in right_mark:
        lines.append(rule(mark, mark, "L", "REWIND_CLEAN"))
    lines.append(rule("#", "#", "H", "STOP"))

    # Move to the right boundary, remembering the left symbol in the state.
    for i in range(n):
        lines.extend(["", f"GO_RIGHT_{i}:"])
        for symbol in alphabet:
            lines.append(rule(symbol, symbol, "R", f"GO_RIGHT_{i}"))
        for mark in left_mark + right_mark:
            lines.append(rule(mark, mark, "R", f"GO_RIGHT_{i}"))
        lines.append(rule("#", "#", "L", f"FIND_RIGHT_{i}"))

    # Find the rightmost unprocessed symbol. If none remains, the selected
    # left symbol is the unique middle character of an odd-length remainder.
    for i in range(n):
        lines.extend(["", f"FIND_RIGHT_{i}:"])
        for j, mark in enumerate(right_mark):
            lines.append(rule(mark, mark, "L", f"FIND_RIGHT_{i}"))
        for j, symbol in enumerate(alphabet):
            lines.append(rule(symbol, right_mark[j], "L", f"RETURN_LEFT_{i}_{j}"))
        for j, mark in enumerate(left_mark):
            lines.append(rule(mark, alphabet[j], "L", "REWIND_CLEAN"))

    # Walk back to the current left marker; replace it with the selected right
    # character, then scan right to the selected right marker and replace that
    # with the original left character.
    for i in range(n):
        for j in range(n):
            state = f"RETURN_LEFT_{i}_{j}"
            lines.extend(["", f"{state}:"])
            for symbol in alphabet:
                lines.append(rule(symbol, symbol, "L", state))
            for mark in left_mark:
                lines.append(rule(mark, left_mark[j], "R", f"GO_TO_RIGHT_MARK_{i}_{j}"))

            state = f"GO_TO_RIGHT_MARK_{i}_{j}"
            lines.extend(["", f"{state}:"])
            for symbol in alphabet:
                lines.append(rule(symbol, symbol, "R", state))
            for mark in left_mark:
                lines.append(rule(mark, mark, "R", state))
            for mark in right_mark:
                lines.append(rule(mark, right_mark[i], "L", "REWIND_LEFT"))

    # Return to the left edge and start another swap round.
    lines.extend(["", "REWIND_LEFT:"])
    for symbol in alphabet + left_mark + right_mark:
        lines.append(rule(symbol, symbol, "L", "REWIND_LEFT"))
    lines.append(rule("#", "#", "R", "FIND_LEFT"))

    # Rewind to the left boundary and remove all temporary marks.
    lines.extend(["", "REWIND_CLEAN:"])
    for symbol in alphabet + left_mark + right_mark:
        lines.append(rule(symbol, symbol, "L", "REWIND_CLEAN"))
    lines.append(rule("#", "#", "R", "CLEAN"))

    lines.extend(["", "CLEAN:"])
    for i, symbol in enumerate(alphabet):
        lines.append(rule(left_mark[i], symbol, "R", "CLEAN"))
        lines.append(rule(right_mark[i], symbol, "R", "CLEAN"))
        lines.append(rule(symbol, symbol, "R", "CLEAN"))
    lines.append(rule("#", "#", "H", "STOP"))
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(f"Usage: {Path(sys.argv[0]).name} alphabet [output.tur]", file=sys.stderr)
        print("Example: reverse_string_generator.py abc", file=sys.stderr)
        return 2
    try:
        alphabet = parse_alphabet(args[0])
        output = Path(args[1] if len(args) == 2 else DEFAULT_OUTPUT)
        program = generate(alphabet)
        output.write_text(program, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} for alphabet {{{', '.join(alphabet)}}}.")
    print(f"Transition rules: {sum('->' in line for line in program.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

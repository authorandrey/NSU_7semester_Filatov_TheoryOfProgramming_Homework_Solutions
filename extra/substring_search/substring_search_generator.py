#!/usr/bin/env python3
"""Generate a one-tape Turing machine for searching a fixed substring.

Usage:
    python substring_search_generator.py aababab
    python substring_search_generator.py aababab custom.tur

Output convention (matching the optimized solution to task 1.7):
- on a match, erase the prefix before the leftmost occurrence, restore that
  occurrence, and preserve the suffix;
- if there is no match, erase the entire input word.
"""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_OUTPUT = "substring_search.tur"
ALPHABET = "ab"


def validate_pattern(pattern: str) -> None:
    if not pattern:
        raise ValueError("pattern must be a non-empty word over {a,b}")
    if any(symbol not in ALPHABET for symbol in pattern):
        raise ValueError("pattern must contain only 'a' and 'b'")


def delta(pattern: str, matched: int, symbol: str) -> int:
    """KMP transition: longest proper prefix of pattern that is a suffix."""
    candidate = pattern[:matched] + symbol
    max_length = min(len(pattern) - 1, len(candidate))
    for length in range(max_length, -1, -1):
        if candidate.endswith(pattern[:length]):
            return length
    return 0


def search_state(matched: int) -> str:
    return "Search_0" if matched == 0 else f"Search_{matched}"


def generate_mt(pattern: str) -> str:
    """Return the emulator program for a fixed pattern."""
    validate_pattern(pattern)
    length = len(pattern)
    lines: list[str] = [
        "alphabet = [#, a, b]",
        "tapes = [ right ]",
        "",
        f"// Fixed pattern P = {pattern}",
        "// Search states implement the prefix automaton (KMP).",
        "// A successful search restores the leftmost match; a failed search erases the word.",
        "",
        "START:",
        "    # -> #R Search_0",
        "",
    ]

    # One Search_i state for every proper-prefix length i of P.
    for matched in range(length):
        lines.append(f"{search_state(matched)}:")
        for symbol in ALPHABET:
            if matched == length - 1 and symbol == pattern[-1]:
                # The just-read symbol completes the pattern.
                if length == 1:
                    lines.append(f"    {symbol} -> {symbol}H STOP")
                else:
                    lines.append(f"    {symbol} -> {symbol}L Restore_{length - 1}")
            else:
                next_matched = delta(pattern, matched, symbol)
                lines.append(f"    {symbol} -> #R {search_state(next_matched)}")
        lines.append("    # -> #H STOP")
        lines.append("")

    # Restore the first L-1 symbols of P moving left from the last symbol.
    if length > 1:
        for restore_index in range(length - 1, 0, -1):
            expected_symbol = pattern[restore_index - 1]
            if restore_index == 1:
                next_action = "H STOP"
            else:
                next_action = f"L Restore_{restore_index - 1}"
            lines.append(f"Restore_{restore_index}:")
            for read_symbol in "#ab":
                lines.append(f"    {read_symbol} -> {expected_symbol}{next_action}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(
            f"Usage: {Path(sys.argv[0]).name} PATTERN [output.tur]",
            file=sys.stderr,
        )
        return 2
    pattern = args[0]
    output = Path(args[1] if len(args) == 2 else DEFAULT_OUTPUT)
    try:
        content = generate_mt(pattern)
        output.write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {output} for pattern {pattern!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

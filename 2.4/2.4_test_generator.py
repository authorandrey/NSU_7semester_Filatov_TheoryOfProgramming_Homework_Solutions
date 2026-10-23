#!/usr/bin/env python3
"""Generate multiplication tests for the four-tape base-k machine."""
from __future__ import annotations
import sys
from pathlib import Path

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_OUTPUT = "2.4.test"


def encode_reversed(n: int, k: int) -> str:
    if n == 0:
        return "0"
    out = []
    while n:
        out.append(DIGITS[n % k])
        n //= k
    return "".join(out)


def generate(k: int) -> str:
    if not 2 <= k <= 16:
        raise ValueError("k must be in the range 2..16")
    vals = set(range(min(k ** 3, 27)))
    vals.update({k * k - 1, k * k + k + 1, k ** 3 - 1})
    vals = sorted(v for v in vals if v >= 0)
    lines = [
        f"// Multiplication tests for base {k}; digits are least-significant first.",
        "// Tape 1 and tape 2 are preserved; tape 3 gets the product; tape 4 must be blank.",
    ]
    for a in vals:
        for b in vals:
            aw = encode_reversed(a, k)
            bw = encode_reversed(b, k)
            pw = encode_reversed(a * b, k)
            lines.append(f"mul_{a}_{b} : #{aw}#|#{bw}#|#|# -> #{aw}#|#{bw}#|#{pw}#|#")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print(f"Usage: {Path(sys.argv[0]).name} k [output.test]", file=sys.stderr)
        return 2
    try:
        k = int(args[0])
        content = generate(k)
        output = args[1] if len(args) == 2 else DEFAULT_OUTPUT
        Path(output).write_text(content, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Generated {output} for base {k}: {sum(' : ' in line for line in content.splitlines())} tests.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

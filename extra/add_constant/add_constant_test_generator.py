#!/usr/bin/env python3
"""Generate tests for add_constant_generator.py.
Usage: python add_constant_test_generator.py m k left|right [output.test]
"""
import sys
from pathlib import Path
DIGITS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DEFAULT_OUTPUT='add_constant.test'
def encode(n,base,orientation):
    if n==0: s='0'
    else:
        out=[]
        while n: out.append(DIGITS[n%base]); n//=base
        s=''.join(out)
    return s if orientation=='left' else s[::-1]
def test(name,n,m,k,orientation):
    before=encode(n,m,orientation); after=encode(n+k,m,orientation)
    return f'{name:<25}: #{before}# -> #{after}#'
def generate(m,k,orientation):
    if not 2<=m<=36: raise ValueError('m must be in 2..36')
    if k<0: raise ValueError('k must be nonnegative')
    if orientation not in ('left','right'): raise ValueError("orientation must be 'left' or 'right'")
    nums=sorted({0,1,2,m-1,m,m+1, m*m-1,m*m,m*m+1, max(0,k-1),k,k+1, max(0,m**3-1)})
    lines=[f'// Add constant {k} in base {m}; LSB {orientation}.','// Format: #input# -> #sum#']
    lines += [test(f'test_{i}',n,m,k,orientation) for i,n in enumerate(nums)]
    return '\n'.join(lines)+'\n'
def main():
    a=sys.argv[1:]
    if len(a) not in (3,4):
        print(f'Usage: {Path(sys.argv[0]).name} m k left|right [output.test]',file=sys.stderr); return 2
    try:
        m,k=int(a[0]),int(a[1]); p=Path(a[3] if len(a)==4 else DEFAULT_OUTPUT)
        s=generate(m,k,a[2].lower()); p.write_text(s,encoding='utf-8')
    except (ValueError,OSError) as e: print(f'Error: {e}',file=sys.stderr); return 1
    print(f'Generated {p}. Tests: {sum(x.startswith("test_") for x in s.splitlines())}'); return 0
if __name__=='__main__': raise SystemExit(main())

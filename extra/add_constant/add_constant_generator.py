#!/usr/bin/env python3
"""Generate a one-tape TM that adds constant k to a base-m numeral.
Usage: python add_constant_generator.py m k left|right [output.tur]
Digits 10..35 are A..Z. Input/output are enclosed by # delimiters.
left means the least significant digit is at the left; right means it is at the right.
"""
import sys
from pathlib import Path
DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DEFAULT_OUTPUT = 'add_constant.tur'

def digit(v): return DIGITS[v]
def rule(read, write, move, state): return f'\t{read} -> {write}{move} {state}'
def generate(m, k, orientation):
    if not 2 <= m <= 36: raise ValueError('m must be in 2..36')
    if k < 0: raise ValueError('k must be nonnegative')
    if orientation not in ('left', 'right'): raise ValueError("orientation must be 'left' or 'right'")
    const=[]; n=k
    if n == 0: const=[0]
    while n:
        const.append(n % m); n //= m
    ds=[digit(i) for i in range(m)]
    # Position i is the digit of the constant aligned with the current input cell.
    lines=['// Generated from add_constant_template.txt',f'// Add {k} in base {m}; LSB {orientation}.',f'alphabet = [{", ".join(["#"]+ds)}]', 'tapes = [ right ]','', 'START:', rule('#','#','R','SCAN')]
    if orientation == 'right':
        lines += ['', 'SCAN:']
        for d in ds: lines.append(rule(d,d,'R','SCAN'))
        lines.append(rule('#','#','L','ADD_0_0'))
    else:
        lines += ['', 'SCAN:']
        for d in ds: lines.append(rule(d,d,'H','ADD_0_0'))
        lines.append(rule('#','#','H','STOP'))
    # Generate position/carry states. At each position, the constant digit is fixed.
    maxpos=len(const)+max(2, k.bit_length()+2)
    # For left orientation, START has moved to first digit. For right, at last digit.
    # Empty input is treated as zero; special handling at initial delimiter.
    for i in range(maxpos):
        c=const[i] if i < len(const) else 0
        for carry in range(2):
            st=f'ADD_{i}_{carry}'
            lines += ['', st+':']
            for v,d in enumerate(ds):
                total=v+c+carry; out=digit(total % m); nc=total//m
                move='R' if orientation=='left' else 'L'
                ni=i+1
                lines.append(rule(d,out,move, f'ADD_{ni}_{nc}'))
            # Boundary reached: produce further constant/carry digits, or stop.
            total=c+carry; out=digit(total % m); nc=total//m
            if i < len(const) or carry:
                move='R' if orientation=='left' else 'L'
                lines.append(rule('#',out,move,f'EXT_{i+1}_{nc}'))
            else:
                lines.append(rule('#','#','H','STOP'))
    # Extension states handle the blank beyond the original word / boundary.
    for i in range(1,maxpos+1):
        c=const[i] if i < len(const) else 0
        for carry in range(2):
            st=f'EXT_{i}_{carry}'
            lines += ['', st+':']
            total=c+carry; out=digit(total % m); nc=total//m
            move='R' if orientation=='left' else 'L'
            if i < len(const) or nc:
                lines.append(rule('#',out,move,f'EXT_{i+1}_{nc}'))
            else:
                lines.append(rule('#','#','H','STOP'))
    return '\n'.join(lines)+'\n'
def main():
    a=sys.argv[1:]
    if len(a) not in (3,4):
        print(f'Usage: {Path(sys.argv[0]).name} m k left|right [output.tur]',file=sys.stderr); return 2
    try:
        m,k=int(a[0]),int(a[1]); output=Path(a[3] if len(a)==4 else DEFAULT_OUTPUT)
        output.write_text(generate(m,k,a[2].lower()),encoding='utf-8')
    except (ValueError,OSError) as e:
        print(f'Error: {e}',file=sys.stderr); return 1
    print(f'Generated {output} (base {m}, constant {k}, LSB {a[2]}).'); return 0
if __name__=='__main__': raise SystemExit(main())

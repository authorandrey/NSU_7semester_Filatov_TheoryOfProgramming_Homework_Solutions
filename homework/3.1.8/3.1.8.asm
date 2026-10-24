;SMALL_PRIMES = (
;    2, 3, 5, 7, 11, 13,
;    17, 19, 23, 29, 31, 37
;)
;MR_BASES = (
;    2, 325, 9375, 28178,
;    450775, 9780504, 1795265022
;)
;LIMIT = 1 << 64
;
;def mod_pow(a_1, d_1, n):
;    result_1 = 1
;
;    while d_1 > 0:
;        if d_1 % 2 == 1:
;            result_1 = (result_1 * a_1) % n
;
;        a_1 = (a_1 * a_1) % n
;        d_1 //= 2
;
;    return result_1
;
;def miller_rabin(n):
;    d = n - 1
;    s = 0
;    while d % 2 == 0:
;        d //= 2
;        s += 1
;    for a in MR_BASES:
;        a %= n
;        if a == 0:
;            continue
;        res = mod_pow(a, d, n)
;        if res == 1 or res == n - 1:
;            continue
;        for _ in range(s - 1):
;            res = res * res % n
;            if res == n - 1:
;                break
;        else:
;            return False
;    return True
;
;def is_prime(n):
;    if n < 2:
;        return False
;    for p in SMALL_PRIMES:
;        if n % p == 0:
;            return n == p
;    res = miller_rabin(n)
;    if n < LIMIT:
;        return res
;    if not res:
;        return False
;    d = 41
;    while d * d <= n:
;        if n % d == 0 or n % (d + 2) == 0:
;            return False
;        d += 6
;    return True


Read 3
Load =2
Sub 3
JGTZ RET_FALSE  ; if n < 2 then return false

; SMALL_PRIMES
Load =2
Store 12
Load =3
Store 13
Load =5
Store 14
Load =7
Store 15
Load =11
Store 16
Load =13
Store 17
Load =17
Store 18
Load =19
Store 19
Load =23
Store 20
Load =29
Store 21
Load =31
Store 22
Load =37
Store 23

; MR_BASES
Load =2
Store 24
Load =325
Store 25
Load =9375
Store 26
Load =28178
Store 27
Load =450775
Store 28
Load =9780504
Store 29
Load =1795265022
Store 30

; LIMIT
Load =18446744073709551616
Store 31

Load =12
Store 1     ; r1 := SMALL_PRIMES.begin()

FOR_SMALL: Load =24 ; 24 == SMALL_PRIMES.end()
    Sub 1
    JZero CALL_MILLER_RABIN    ; if r1 == end() then exit for
    Load *1
    Store 4         ; r4 = p := SMALL_PRIMES[i]
    Load 3
    Div 4
    Mult 4
    Sub 3
    Mult =-1        ; r0 := (((n // p) * p) - n) * (-1) = n % p
    JZero N_eq_P    ; if n % p == 0 then return  n == p
    Load 1
    Add =1
    Store 1         ; r1++
    Jump FOR_SMALL
N_eq_P: Load 3
    Sub 4
    JZero RET_TRUE
    Jump RET_FALSE
CALL_MILLER_RABIN: Load 3
    Sub =1
    Store 5         ; d := n - 1
    Load =0
    Store 6         ; s := 0
WHILE_d_mod_2: Load 5
    Div =2
    Mult =2
    Sub 5
    Mult =-1        ; r0 := d % 2
    JZero WHILE_d_mod_2_EXEC    ; if d % 2 == 0 execute body
    Jump FOR_MR_BASES_INIT      ; else exit while loop
WHILE_d_mod_2_EXEC: Load 5
    Div =2
    Store 5         ; d //= 2
    Load 6
    Add =1
    Store 6         ; s++
    Jump WHILE_d_mod_2
FOR_MR_BASES_INIT: Load =24
    Store 1         ; r1 := MR_BASES.begin()
FOR_MR_BASES: Load =31          ; 31 == MR_BASES.end()
    Sub 1
    JZero MR_RET_TRUE           ; if MR_BASES ended, return True
    Load *1
    Store 7         ; r0, a := MR_BASES[i]
    Div 3
    Mult 3
    Sub 7
    Mult =-1        ; r0 := a % n
    Store 7         ; a %= n
    JZero FOR_MR_BASES_CONTINUE ; if a == 0 then continue
    ; call mod_pow(a, d, n)
    Load 7
    Store 9
    Load 5
    Store 10        ; a_1 := a, d_1 := d
MOD_POW: Load =1
    Store 11        ; res_1 := 1
MOD_POW_WHILE: Load =0
    Sub 10
    JZero FOR_MR_BASES_IF_OR
    JGTZ FOR_MR_BASES_IF_OR     ; if d_1 <= 0 then exit while and ret res_1
    Load 10
    Div =2
    Mult =2
    Sub 10
    Mult =-1
    Sub =1          ; r0 := d_1 % 2 - 1
    JZero MOD_POW_WHILE_IF_BODY
    Jump MOD_POW_WHILE_END
MOD_POW_WHILE_IF_BODY: Load 11
    Mult 9
    Store 2         ; r2 := res_1 * a_1
    Div 3
    Mult 3
    Sub 2
    Mult =-1        ; r0 := (res_1 * a_1) % n
    Store 11        ; res_1 := (res_1 * a_1) % n
MOD_POW_WHILE_END: Load 9
    Mult 9
    Store 2         ; r2 := a_1 * a_1
    Div 3
    Mult 3
    Sub 2
    Mult =-1        ; r0 := (a_1 * a_1) % n
    Store 9         ; a_1 := (a_1 * a_1) % n
    Load 10
    Div =2
    Store 10        ; d_1 //= 2
    Jump MOD_POW_WHILE  ; res := mod_pow(a, d, n)
FOR_MR_BASES_IF_OR: Load 11
    Store 8         ; res := res_1
    Sub =1
    JZero FOR_MR_BASES_CONTINUE     ; if res_1 == 1 then continue
    Load 8
    Sub 3
    Add =1
    JZero FOR_MR_BASES_CONTINUE     ; if res_1 == n-1 then continue
FOR_MR_BASES_FOR_INIT: Load 6
    Sub =1
    Store 2         ; r2 := s-1
; for _ in range(s - 1):
FOR_MR_BASES_FOR: Load 2
    JZero MR_RET_FALSE      ; if for did not break (else block) return False
    Load 8
    Mult 8
    Store 32         ; r32 := res * res
    Div 3
    Mult 3
    Sub 32
    Mult =-1        ; r0 := (res * res) % n
    Store 8         ; res := (res * res) % n
    Sub 3
    Add =1
    JZero FOR_MR_BASES_CONTINUE    ; if res == n-1 then break (equal to continue)
    Load 2
    Sub =1
    Store 2         ; r2--
    Jump FOR_MR_BASES_FOR
FOR_MR_BASES_CONTINUE: Load 1
    Add =1
    Store 1         ; r1++
    Jump FOR_MR_BASES
MR_RET_FALSE: Load =0
    Store 8         ; res := miller_rabin(n)
    Jump IF_LIM
MR_RET_TRUE: Load =1
    Store 8         ; res := miller_rabin(n)
IF_LIM: Load 31
    Sub 3
    JGTZ IF_LIM_RET
    ; if not res
    Load 8
    JZero RET_FALSE ; if not res: return False
    Load =41
    Store 5         ; d := 41
    Jump WHILE
IF_LIM_RET: Load 8
    JZero RET_FALSE
    Jump RET_TRUE
; while d * d <= n
WHILE: Load 5
    Mult 5
    Sub 3
    JGTZ RET_TRUE   ; if d*d>n then return True
    Load 3
    Div 5
    Mult 5
    Sub 3
    Mult =-1
    JZero   RET_FALSE   ; if n%d==0 then return False
    Load 5
    Add =2
    Store 1         ; r1 := d + 2
    Load 3
    Div 1
    Mult 1
    Sub 3
    Mult =-1
    JZero RET_FALSE     ; if n%(d+2)==0 then return False
    Load 5
    Add =6
    Store 5         ; d += 6
    Jump WHILE
RET_FALSE: Write =0
    Halt 0
RET_TRUE: Write =1
    Halt 0
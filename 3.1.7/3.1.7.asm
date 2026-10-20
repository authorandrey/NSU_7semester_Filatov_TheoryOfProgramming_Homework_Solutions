;long long binpow(long long base, long long exp) {
;    long long res = 1;
;    while (exp > 0) {
;        if (exp % 2 == 1)
;            res *= base;
;        base *= base;
;        exp /= 2;
;    }
;    return res;
;}


; Data Model
;0: r0
;1: result
;2: base
;3: exp

Load =0
Read 2
Sub 2
JZero END   ; 0^0 - invalid input
JGTZ END    ; (-a)^{-a} = 1 / (-a)^a = 0|1|-1. Suppoze n < 0 - invalid input

Load =1
Store 1     ; result := 1
Load 2
Store 3     ; exp := n

WHILE: Load =0
    Sub 3
    JZero END
    JGTZ END    ; if exp <= 0 (-exp >= 0) then return result
    Load 3      ; r0 := exp
    Div =2
    Mult =2
    Sub 3
    Mult =-1    ; r0 := ((exp // 2) * 2 - exp) * (-1) = exp % 2
    Sub =1
    JZero MULT_RES  ; if exp%2==1 then result *= base
    Jump WHILE_END
MULT_RES: Load 1
    Mult 2
    Store 1     ; result *= base
WHILE_END: Load 2
    Mult 2
    Store 2     ; base *= base
    Load 3
    Div =2
    Store 3     ; exp //= 2
    Jump WHILE
END: Write 1
    Halt 0
; r1 ::= C - encoded program (defined postfactum)
; r2 ::= C - remaining C after extracting an opcode or an argument
; r3 ::= base = 1000
; r4 ::= len(A) - length of the program (defined postfactum)
;
; while r4 != 0:
;    d := r2 % r3
;    r2 := r2 // (999 + 1)
;    d -> OUT
;    r4--
;    if r4 == len(A) - 1:
;        r1 -> OUT (C)

; r1, r2 := C - encoded program
Load =9023004004001009004002001021028023002004005002007021007004006010002002006004003013005002005004003016002002027024063009004002032024004002004004064001003004001006999001002004001004001
Store 1
Store 2

Load =999
Add =1              ; Numbers must be lower than 1000
Store 3             ; r3 := base
Load =64
Store 4             ; r4 := len(A)

WHILE: Load 4
    JZero END       ; if r4 == 0 then program is endede
    Load 4
    Sub =63
    JZero SPECIAL   ; if r4 == len(A) - 1 then print C
    ; in other cases output program
    Load 2
    Div 3
    Store 5         ; r5 := r2 // r3
    Load 5
    Mult 3
    Store 6         ; r6 := r2 // r3 * r2
    Load 2
    Sub 6
    Store 7
    Write 7         ; r7 := r2 - (r2 // r3 * r2) = r2 % r3 -> OUT
    Load 5
    Store 2         ; r2 := r2 >> 1 (base 1000)
    Jump AFTER_OUTPUT
SPECIAL: Write 1
AFTER_OUTPUT: Load 4
    Sub =1
    Store 4         ; r4--
    Jump WHILE
END: Halt 0
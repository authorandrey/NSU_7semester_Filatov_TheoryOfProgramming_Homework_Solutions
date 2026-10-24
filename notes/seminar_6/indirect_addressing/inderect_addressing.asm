; Calculate scalar product
; In: n>0, a_1, ..., a_n, b_1, ..., b_n
; Out: \sum_{i=1}^n a_i*b_i

; Memory Model
; 0: r0
; 1: n
; 2: sum
; 3: something
; 4...n+3: a_1, ..., a_n

Read 1      ; r1 := n
Load =0
Sub 1
JZero END
JGTZ END    ; exit if n<=0 (invalid)

Load 1
READ_A: Sub 1
    JZero SUM_INIT  ; exit read_a if r0 == n
    Add =3          ; r0 := &arr[i]
    Read *0
    Sub =2          ; r0 := ++i
    Jump READ_A
SUM_INIT: Load =3
    Store 3         ; r3 := &arr[1]
SUM: Load 3
    Sub =4
    Sub 1           ; r0 := r3 - n - 4
    JZero PRINT     ; exit sum if r3 == arr.end()
    Read 0
    Mult *3
    Add 2
    Store 2         ; sum += a[i] * read()
    Load 3
    Add =1
    Store 3         ; r3++
    Jump SUM
PRINT: Write 2
END: Halt 0
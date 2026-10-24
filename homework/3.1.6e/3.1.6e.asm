;def counting_sort(arr):
;    min_val, max_val = -100, 100
;    range_size = max_val - min_val + 1
;    count = [0] * range_size
;
;    for x in arr:
;        count[x - min_val] += 1
;
;    pos = 0
;    for idx in range(range_size):
;        value = idx + min_val
;        for _ in range(count[idx]):
;            arr[pos] = value
;            pos += 1
;    return arr


; Data Model
;0: r0
;1: trash | a_i | iterator
;2: n | a_i
;3 ... 203: arr
;204: [arr.end()]

Read 2
Load =0
Sub 2
JZero END
JGTZ END    ; if n <= 0 then exit

READ_DATA: Load 2
    JZero PRINT_INIT; if n == 0 then goto PRINT
    Read 1          ; r1 := read() = a_i
    Load 1
    Add =103        ; r0 := &arr[a_i]
    Store 1         ; r1 := &arr[a_i]
    Load *0         ; r0 := arr[a_i]
    Add =1
    Store *1        ; arr[a_i]++
    Load 2
    Sub =1
    Store 2         ; n--
    Jump READ_DATA
PRINT_INIT: Load =3
    Store 1         ; r1 := arr.begin()
PRINT: Load =204
    Sub 1
    JZero END       ; if r1 == arr.end() then exit PRINT
    Load 1
    Sub =103
    Store 2         ; r2 := a_i
    Load *1         ; r0 := arr[a_i]
; if arr[a_i] = k > 0 then print a_i k times
PRINT_NUM: JZero PRINT_AFTER_NUM    ; if r0 == 0 then end print a_i
    Write 2         ; print a_i
    Sub =1          ; r0--
    Jump PRINT_NUM
PRINT_AFTER_NUM: Load 1
    Add =1
    Store 1         ; r1++
    Jump PRINT
END: Halt 1
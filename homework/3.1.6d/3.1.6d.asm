;public class Heap {
;    public static void sort(Comparable[] pq) {
;        int n = pq.length;
;        for (int k = n/2; k >= 1; k--)
;            sink(pq, k, n);
;        int k = n;
;        while (k > 1) {
;            exch(pq, 1, k--);
;            sink(pq, 1, k);
;        }
;    }
;
;    private static void sink(Comparable[] pq, int l, int m) {
;        while (2*l <= m) {
;            int j = 2*l;
;            if (j < m && less(pq, j, j+1)) j++;
;            if (!less(pq, l, j)) break;
;            exch(pq, l, j);
;            l = j;
;        }
;    }
;}
;
;sort(arr)


; Data Model
;0: r0
;1: trash | iterator
;2: &end
;3: n
;4: k
;5: l
;6: m
;7: j
;8: call (from what place was sink called last time)
;9 ... 9+n-1: arr

Load =0
Read 3
Sub 3           ; r3 := n
JZero END
JGTZ END		; n <= 0 ==> exit (invalid size)

Load 3
Add =9
Store 2			; r2 := 9 + n (arr_a.end())

Load =9
Store 1			; r1 := 9 (arr_a.begin())

READ_ARRAY: Load 2
	Sub 1
	JZero SORT		; if r2 == r1 exit read
	Read *1
	Load 1
	Add =1
	Store 1		; r1++
	Jump READ_ARRAY
SORT: Load 3
    Div =2
    Store 4     ; r4 := k = n // 2
FOR: Load =1
    Sub 4
    JGTZ FOR_END    ; if k < 1 then exit for
    Load 4
    Store 5
    Load 3
    Store 6     ; l := k, m := n
    Load =0
    Store 8     ; call = 0 (call from for)
    Jump SINK   ; call sink(k, n)
FOR_CALL_END: Load 4
    Sub =1
    Store 4     ; k--
    Jump FOR
FOR_END: Load 3
    Store 4     ; k := n
WHILE_k_gt_1: Load =1
    Sub 4
    JZero PRINT_INIT
    JGTZ PRINT_INIT   ; if k <= 1 then exit while and exit sort
    ; SWAP
    Load 4
    Add =8
    Load *0
    Store 1     ; r1 := arr[k]
    Load 9      ; r0 := arr[1]
    Store 2     ; r2 := arr[1]
    Load 1
    Store 9     ; arr[1] := arr[k]
    Load 4
    Add =8
    Store 1     ; r1 := &arr[k]
    Load 2
    Store *1    ; arr[k] (= *r1) := arr[1] (= r2)
    ; k--
    Load 4
    Sub =1
    Store 4
    ; CALL sink(1, k)
    Load =1
    Store 5     ; l := 1
    Load 4
    Store 6     ; m := k
    Load =1
    Store 8     ; call := 1 (call sink from while)
    Jump SINK
SINK: Load =2
    Mult 5
    Sub 6
    JGTZ CALL_RETURN    ; if 2*l-m > 0 then exit SINK
    Load =2
    Mult 5
    Store 7     ; j := 2*l
    ; if (j < m && less(pq, j, j+1)) j++;
    Load 7
    Sub 6
    JZero IF_BREAK
    JGTZ IF_BREAK       ; if j-m>=0 then do not do IF
    Load 7
    Add =8
    Store 1     ; r1 := &arr[j]
    Add =1
    Store 2     ; r2 := &arr[j+1]
    Load *1
    Sub *2
    JZero IF_BREAK
    JGTZ IF_BREAK       ; if a[j] >= a[j+1] then do not do IF
    Load 7
    Add =1
    Store 7     ; j++
; if (!less(pq, l, j)) break;
IF_BREAK: Load 7
    Add =8
    Load *0
    Store 1     ; r1 := arr[j]
    Load 5
    Add =8
    Load *0     ; r0 := arr[l]
    Sub 1       ; r0 := arr[l] - arr[j]
    JZero CALL_RETURN
    JGTZ CALL_RETURN    ; if a[l] >= a[j] then return from SINK
    ; SWAP if not break executed
    Load 7
    Add =8
    Load *0
    Store 1     ; r1 := arr[j]
    Load 7
    Add =8      ; r0 := &arr[j]
    Store 2     ; r2 := &arr[j]
    Load 5
    Add =8
    Load *0     ; r0 := arr[l]
    Store *2    ; arr[j] (= *r2) := arr[l] (= r0)
    Load 5
    Add =8
    Store 2     ; r2 := &arr[l]
    Load 1      ; r0 := arr[j] (previous)
    Store *2    ; arr[l] (= *r2) := arr_previous[j] (= r0)
    ; l = j
    Load 7
    Store 5
    ; goto WHILE
    Jump SINK
CALL_RETURN: Load 8
    JZero FOR_CALL_END  ; return from sink(k, n)
    Jump WHILE_k_gt_1   ; return from sink(1, k)
PRINT_INIT: Load =9
    Store 1     ; r1 := arr.begin()
    Add 3
    Store 2     ; r2 := arr.end()
PRINT: Load 2
    Sub 1
    JZero END   ; if r1 == r2 then exit print
    Write *1
    Load 1
    Add =1
    Store 1     ; r1++
    Jump PRINT
END: Halt 0
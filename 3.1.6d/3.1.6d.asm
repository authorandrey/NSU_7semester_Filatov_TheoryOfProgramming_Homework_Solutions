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
;8: call
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
    Load =1
    Store 8     ; call = 1 (call from for)
    Jump SINK   ; call sink(k, n)
FOR_CALL_END: Load 4
    Sub =1
    Store 4     ; k--
    Jump FOR
FOR_END: Load 3
    Store 4     ; k := n
WHILE_k_gt_1: Load =1
    Sub 4
    JZero END_WHILE_k_gt_1
    JGTZ END_WHILE_k_gt_1   ; if k <= 1 then exit while
    Load 4
    Add =8
    Store *1    ; r1 := arr[k]
    Load 9      ; r0 := arr[1]
    Store 2     ; r2 := arr[1]
    Load 1
    Store 9     ; arr[1] := arr[k]
    
SINK: 
;proc sort(l,r)
;	if r>l then
;		m:= (l+r)/2;
;		sort(l,m);
;		m:= (l+r)/2; 	; Counter modifications of sort calls
;		sort(m+1,r);
;		m:= (l+r)/2; 	; Counter modifications of sort calls
;		k := l;
;		i := l;
;       j := m + 1;
;		while i<=m and j<=r
;			if a[i].key<a[j].key then
;				b[k]:=a[i];
;				i:=i+1;
;			else
;				b[k]:=a[j];
;				j:=j+1;
;			k:=k+1;
;		while i<=m
;			b[k]:=a[i];
;			i:=i+1;
;			k:=k+1;
;		while j<=r
;			b[k]:=a[j];
;			j:=j+1;
;			k:=k+1;
;		a[l..r] := b[l..r];
;sort(1, n);


; Data Model
;0: r0
;1: &start_a | iterator
;2: &end_a
;3: &start_b | iterator
;4: &end_b
;5: &l
;6: &r
;7: &cs
;8: m
;9: k
;10: i
;11: j
;12..12+n-1: array_a
;12+n..12+2n-1: array_b
;12+2n...infty: stack (l, r, cs)
;
;stack: l, r, cs
;cs: code of the last pseudo-called function
;local: m, k, i, j


Load =0
Read 1
Sub 1
JZero END
JGTZ END		; n <= 0 ==> exit (invalid size)

Load 1
Add =12
Store 2			; r2 := 12 + n (arr_a.end())
Add 1
Store 4			; r4 := 12 + 2n (arr_b.end())

Load =12
Store 1			; r1 := 12 (arr_a.begin())

READ_ARRAY: Load 2
	Sub 1
	JZero INIT_SORT		; if r2 == r1 exit read
	Read *1
	Load 1
	Add =1
	Store 1		; r1++
	Jump READ_ARRAY
INIT_SORT: Load 4
	Store 5		; r5 := &l
	Add =1
	Store 6		; r6 := &r
	Add =1
	Store 7		; r7 := &cs
	Load =1
	Store *5	; l := 1
	Load 2
	Sub =12
	Store *6	; r := n
	Load =0
	Store *7	; cs := 0 (call from MAIN)
SORT: Load *5
	Sub *6
	JZero CALL_STACK_RETURN
	JGTZ CALL_STACK_RETURN		; if r - l <= 0 (l - r >= 0) do not call IF
	Load *5
	Add *6
	Div =2
	Store 8		; r8 = m := (l + r) // 2
CALL_SORT_1: Load *5
	Store 1		; r1 := l
	Load 5
	Add =3
	Store 5		; &l += 3 (next l)
	Load 1
	Store *5	; l := l_previous
	Load 6
	Add =3
	Store 6		; &r += 3 (next r)
	Load 8
	Store *6	; r := m
	Load 7
	Add =3
	Store 7		; &cs += 3 (next cs)
	Load =1
	Store *7	; cs := 1 (call from sort(l, m))
	Jump SORT	; call sort(l, m)
CALL_SORT_2: Load *5
	Add *6
	Div =2
	Store 8		; m := (l + r) // 2
	Load *6
	Store 1		; r1 := r
	Load 5
	Add =3
	Store 5		; &l += 3 (next l)
	Load 8
	Add =1
	Store *5	; l := m + 1
	Load 6
	Add =3
	Store 6		; &r += 3 (next r)
	Load 1
	Store *6	; r := r_previous
	Load 7
	Add =3
	Store 7		; &cs += 3 (next cs)
	Load =2
	Store *7	; cs := 2 (call from sort(m+1, r))
	Jump SORT	; call sort(m+1, r)
CALL_STACK_RETURN: Load *7
	JZero PRINT_INIT	; cs == 0 ==> exit sort(1, n) procedure
	Store 1		; r1 := cs
	Load 5
	Sub =3
	Store 5		; &l -= 3
	Load 6
	Sub =3
	Store 6		; &r -= 3
	Load 7
	Sub =3
	Store 7		; &cs -= 3
	Load 1
	Sub =1
	JZero CALL_SORT_2		; cs == 1 ==> exit call sort(l, m)
	; cs == 2 ==> exit call sort(m+1, r) and goto SORT_AFTER_CALL
SORT_AFTER_CALL: Load *5
	Add *6
	Div =2
	Store 8		; m := (l + r) // 2
	Load *5
	Store 9
	Store 10	; k, i := l
	Load 8
	Add =1
	Store 11	; j := m + 1
WHILE_and: Load 10
	Sub 8
	JGTZ WHILE_i_le_m
	Load 11
	Sub *6
	JGTZ WHILE_i_le_m	; if i-m>0 or j-r>0 exit while
IF_lt: Load 11
	Add =11
	Load *0
	Store 1		; r1 := arr_a[j]
	Load 10
	Add =11
	Load *0		; r0 := arr_a[i]
	Sub 1
	JZero ELSE_lt
	JGTZ ELSE_lt	; if arr_a[i]-arr_a[j]>=0 then do ELSE
	Load 2
	Add 9
	Sub =1
	Store 3		; r3 := &arr_b[k] (arr_a.end() = arr_b.begin())
	Load 10
	Add =11
	Load *0		; r0 := arr_a[i]
	Store *3	; arr_b[k] (=*r3)
	Load 10
	Add =1
	Store 10	; i++
	Jump IF_END
ELSE_lt: Load 2
	Add 9
	Sub =1
	Store 3		; r3 := &arr_b[k] (arr_a.end() = arr_b.begin())
	Load 11
	Add =11
	Load *0		; r0 := arr_a[j]
	Store *3	; arr_b[k] (=*r3) = r0
	Load 11
	Add =1
	Store 11	; j++
IF_END: Load 9
	Add =1
	Store 9		; k++
	Jump WHILE_and
WHILE_i_le_m: Load 10
	Sub 8
	JGTZ WHILE_j_le_r	; if i-m>0 exit while
	Load 2
	Add 9
	Sub =1
	Store 3		; r3 := &arr_b[k] (arr_a.end() = arr_b.begin())
	Load 10
	Add =11
	Load *0		; r0 := arr_a[i]
	Store *3	; arr_b[k] := arr_a[i]
	Load 10
	Add =1
	Store 10	; i++
	Load 9
	Add =1
	Store 9		; k++
	Jump WHILE_i_le_m
WHILE_j_le_r: Load 11
	Sub *6
	JGTZ COPY_INIT	; if j-r>0 exit while
	Load 2
	Add 9
	Sub =1
	Store 3		; r3 := &arr_b[k] (arr_a.end() = arr_b.begin())
	Load 11
	Add =11
	Load *0		; r0 := arr_a[j]
	Store *3	; arr_b[k] := arr_a[j]
	Load 11
	Add =1
	Store 11	; j++
	Load 9
	Add =1
	Store 9		; k++
	Jump WHILE_j_le_r
COPY_INIT: Load *5
	Add =11
	Store 1		; r1 := &arr_a[l]
	Load *5
	Add 2
	Sub =1
	Store 3		; r3 := &arr_b[l]
	Load *6
	Sub *5
	Add =1
	Store 8		; r8 := r - l + 1
COPY: Load 8
	JZero CALL_STACK_RETURN		; if r-l+1==0 then exit recursion iteration
	Load *3
	Store *1	; arr_a[ITER] := arr_b[ITER]
	Load 1
	Add =1
	Store 1		; r1++
	Load 3
	Add =1
	Store 3		; r3++
	Load 8
	Sub =1
	Store 8		; r8--
	Jump COPY
PRINT_INIT: Load =12
	Store 1		; r1 := arr_a.begin()
PRINT: Load 2
	Sub 1
	JZero END	; if r2 == r1 then exit print
	Write *1
	Load 1
	Add =1
	Store 1		; r1++
	Jump PRINT
END: Halt 0
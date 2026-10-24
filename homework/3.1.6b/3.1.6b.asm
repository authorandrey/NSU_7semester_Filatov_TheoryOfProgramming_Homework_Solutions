;procedure sort(l,r: longint);
;    var
;        i,j,x,y: longint;
;    begin
;        i:=l;
;        j:=r;
;        x:=a[(l+r) div 2];
;        repeat
;        while a[i]<x do
;            inc(i);
;        while x<a[j] do
;            dec(j);
;        if not(i>j) then
;            begin
;            y:=a[i];
;            a[i]:=a[j];
;            a[j]:=y;
;            inc(i);
;            j:=j-1;
;            end;
;        until i>j;
;        if l<j then
;            sort(l,j);
;        if i<r then
;            sort(i,r);
;    end;
;
;begin
;    max = len(array)
;    sort(1,max);
;end;

Read 1
Load =0
Sub 1
JZero END
JGTZ END    ; n <= 0 ==> end
Load 1
Add =10
Store 2     ; r2 := 10 + n, end of array + 1

Load =10
Store 1     ; r1 := 10, start of array. And also r1 is a helping register

READ_ARRAY: Load 2
    Sub 1
    JZero INIT_SORT ; r1 == r2 => end read
    Read *1         ; buf[r1] <- In
    Load =1
    Add 1
    Store 1         ; r1 += 1
    Jump READ_ARRAY
INIT_SORT: Load =1
    Store 3         ; r3 := l = 1
    Load 2
    Store 4         ; r4 := &r = 10 + n
    Sub =10
    Store *4        ; r (= *r4) := n
    Load 4
    Add =2
    Store 9         ; r9 := &cs
    Load =0
    Store *9        ; cs := 0 (call from MAIN)
SORT: Load 4
    Add =1
    Store 5         ; r5 := &i = &r + 1 (next i on call stack)
    Load 3
    Store *5        ; i (= *r5) := l
    Load *4
    Store 6         ; r6 := j = last r on call stack
    Load 3
    Add *4
    Div =2          ; r0 := (l+r) // 2
    Add =9          ; r0 := &a[(l+r) // 2]
    Load *0
    Store 7         ; r7 := x = a[(l+r) // 2]
REPEAT: Jump WHILE_i
WHILE_i: Load *5    ; r0 := i
    Add =9          ; r0 := &a[i]
    Load *0         ; r0 := a[i]
    Sub 7
    JGTZ WHILE_j
    JZero WHILE_j   ; if a[i] - x >= 0 end while
    Load *5
    Add =1
    Store *5         ; i++
    Jump WHILE_i
WHILE_j: Load 6     ; r0 := j
    Add =9          ; r0 := &a[j]
    Load *0
    Sub 7
    Mult =-1         ; r0 := (a[j] - x) * (-1)
    JGTZ IF_not_i_gt_j
    JZero IF_not_i_gt_j ; if x - a[j] >= 0 end while
    Load 6
    Sub =1
    Store 6         ; j--
    Jump WHILE_j
IF_not_i_gt_j: Load *5
    Sub 6
    JGTZ UNTIL      ; if i > j do not do IF
    Load *5         ; r0 := i
    Add =9          ; r0 := &a[i]
    Load *0         ; r0 := a[i]
    Store 8         ; r8 := y = a[i]
    Load *5
    Add =9
    Store 1         ; r1 := &a[i]
    Load 6
    Add =9          ; r0 := &a[j]
    Load *0         ; r0 := a[j]
    Store *1        ; a[i] := a[j]
    Load 6
    Add =9
    Store 1         ; r1 := &a[j]
    Load 8
    Store *1        ; a[j] := y
    Load *5
    Add =1
    Store *5        ; i++
    Load 6
    Sub =1
    Store 6         ; j--
UNTIL: Load *5
    Sub 6
    JGTZ IF_l_lt_j  ; if i > j end repeat
    Jump REPEAT
IF_l_lt_j: Load 3
    Sub 6
    JGTZ IF_i_lt_r
    JZero IF_i_lt_r ; if l - j >= 0 do not do IF
    ; l = l
    Load 4
    Add =3
    Store 4          ; r4 := &r + 3 (next r)
    Load 6
    Store *4        ; r := j
    Load 9
    Add =3
    Store 9         ; &cs += 3
    Load =1
    Store *9        ; cs := 1 (call from sort(l, j))
    Jump SORT       ; call sort(l, j)
IF_i_lt_r: Load *5
    Sub *4
    JGTZ CALL_STACK_RETURN
    JZero CALL_STACK_RETURN    ; if i - r >= 0 do not do IF
    Load *4
    Store 1         ; r1 := r
    Load 4
    Add =3
    Store 4         ; &r += 3
    Load 1
    Store *4        ; r := r1 = r_previous
    Load *5
    Store 3         ; l := i
    Load 5
    Add =3
    Store 5         ; &i += 3
    Load 9
    Add =3
    Store 9         ; &cs += 3
    Load =2
    Store *9        ; cs := 2 (call from sort(i, r))
    Jump SORT       ; call sort(i, r)
CALL_STACK_RETURN: Load *9
    JZero PRINT_INIT    ; cs == 0 => exit sort(1, max)
    Load 4
    Sub =3
    Store 4         ; &r -= 3 (previous r)
    Load 5
    Sub =3
    Store 5         ; &i -= 3 (previous i)
    Load *9
    Store 1         ; r1 := cs
    Load 9
    Sub =3
    Store 9         ; &cs -= 3 (previous cs)
    Load 1
    Sub =1
    JZero IF_i_lt_r     ; cs == 1 => exit sort(l, j)
    Jump CALL_STACK_RETURN
PRINT_INIT: Load =10
    Store 1
PRINT: Load 2
    Sub 1
    JZero END       ; r2 == r1 => end print
    Write *1
    Load 1
    Add =1
    Store 1         ; r1 += 1
    Jump PRINT
END: Halt 0
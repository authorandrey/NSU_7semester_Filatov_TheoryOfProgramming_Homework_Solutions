Read 1	; x

Load 1
JZero END_0		; x == 0 => Out: 0

Load =3
Store 2         ; r2 := 3 - reference to the [last + 1] cell of buffer

WHILE: Load =0
	Sub 1
	JGTZ WRITE_RESULT
	JZero WRITE_RESULT	; exit if x <= 0
	Load 1
	Div =2
	Mult =2
	Sub 1
	Mult =-1	; r0 := x mod 2 = ((x // 2) * 2 - x) * -1
	Store *2    ; buffer[r2] := r0
    Load =1
    Add 2
    Store 2     ; r2 += 1
	Load 1
	Div =2
	Store 1		; x := x // 2
	Jump WHILE
WRITE_RESULT: Load =3
    Sub 2
    JZero END   ; r2 == 3, all the buffer was read
    Load 2
    Sub =1
    Store 2     ; r2 -= 1
    Write *2    ; OUT <- buffer[last]
    Jump WRITE_RESULT
END_0: Write =0
END: Halt 0
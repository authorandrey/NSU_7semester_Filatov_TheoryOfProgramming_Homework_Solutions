Read 1	; x

WHILE: Load =0
	Sub 1
	JGTZ END
	JZero END	; exit if x <= 0
	Load 1
	Div =2
	Mult =2
	Sub 1
	Mult =-1	; r0 := x mod 2 = ((x // 2) * 2 - x) * -1
	Write 0
	Load 1
	Div =2
	Store 1		; x := x // 2
	Jump WHILE
END: Halt 0	
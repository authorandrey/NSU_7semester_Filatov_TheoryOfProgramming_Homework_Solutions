Read 1	; n
Load =0
Sub 1
JZero SUCCESS	; n = 0
JGTZ SUCCESS	; n < 0

Read 2	; a_i

Load 1
Sub =1
Store 1	; n := n-1

WHILE: Load 1
	JZero SUCCESS
	Read 3	; r3 := a_{i+1}
	Load 2
	Sub 3	; r0 := a_i - a_{i+1}
	JGTZ FAIL
	Load 1
	Sub =1
	Store 1	; n := n-1, equivalent to i++
	Load 3
	Store 2 ; r2 := a_{i+1}
	Jump WHILE
SUCCESS: Write =1
	Halt 0
FAIL: Write =0
	Halt 0
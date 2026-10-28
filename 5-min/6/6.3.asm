Read 1		; r1 := n
Load =3
Store 2		; r2 := 3 = arr.begin()
Load 1
Add =3
Store 1		; r1 := n + 3 = arr.end()
READ_LOOP: Load 1
	Sub 2
	JZero READ_DONE		; if r2 == arr.end() then exit read
	Read *2
	Load 2
	Add =1
	Store 2				; r2--
	Jump READ_LOOP
READ_DONE: Load =2
	Store 2				; r2 := arr.begin() - 1
    Load 1
    Sub =1
    Store 1             ; r3 := &arr.last
OUTPUT_LOOP: Load 1
	Sub 2
	JZero END
	Write *1
	Load 1
	Sub =1
	Store 1				; r1--
	Jump OUTPUT_LOOP
END: Halt 0
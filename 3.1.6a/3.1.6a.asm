;for i:=2 to n-1
; for j:=n downto i
;    if a[j-1].key > a[j].key then 
;       a[j-1] :=: a[j] 



;include Irvine32.inc
;include msvcrt.inc
;includelib ...
;.data
;	fmt_out db "%d", 10, 0
;	n       dd ?
;	array   dd 100 dup(?)
;.code
;Main PROC uses ebx esi edi
;	call ReadInt
;	mov n, eax
;	
;	mov ecx, eax
;	mov esi, 0
;READ_LOOP:
;	call ReadInt
;	mov array[esi*4], eax
;	inc esi
;	cmp esi, ecx
;	jl READ_LOOP
;
;	; for i:=2 to n-1
;	mov ecx, 2
;OUTER_LOOP:
;	cmp ecx, n
;	jge END_SORT
;	
;	; for j:=n downto i
;	mov edx, n
;INNER_LOOP:
;	cmp edx, ecx
;	jl NEXT_I
;	; if a[j-1].key > a[j].key
;	mov eax, array[edx*4 - 8]
;	cmp eax, array[edx*4 - 4]
;	jle NO_SWAP
;	; a[j-1] :=: a[j]
;	mov ebx, array[edx*4 - 4]
;	mov array[edx*4 - 4], eax
;	mov array[edx*4 - 8], ebx
;NO_SWAP:
;	dec edx
;	jmp INNER_LOOP
;NEXT_I:
;	inc ecx
;	jmp OUTER_LOOP
;	
;END_SORT:
;	mov esi, 0
;PRINT_LOOP:
;	cmp esi, n
;	jge DONE
;	invoke crt_printf, addr fmt_out, array[esi*4]
;	inc esi
;	jmp PRINT_LOOP
;DONE:
;	ret
;Main ENDP
;start:
;	call Main
;	ret
;END

Read 1	    ; n
Load =1
Store 8	    ; idx := 1

READ_LOOP: Load 8
	Sub 1
	JGTZ INIT_SORT
	Load 8
	Add =9
	Store 9
	Read *9
	Load 8
	Add =1
	Store 8
	Jump READ_LOOP
INIT_SORT: Load =2
	Store 2	    ; i := 2
OUTER: Load 1
	Sub 2
	JGTZ INNER_INIT
	JZero INNER_INIT
	Jump PRINT_INIT
INNER_INIT: Load 1
	Store 3	    ; j := n
INNER: Load 3
	Sub 2
	JGTZ CHECK
	JZero CHECK
	Jump NEXT_I
CHECK: Load 3
	Add =9
	Store 4	    ; r4 := 9+j
	Load *4
	Store 7	    ; r7 := a[j]
	Load 4
	Sub =1
	Store 5	    ; r5 := 9+j-1
	Load *5
	Store 6	    ; r6 := a[j-1]
	Load 6
	Sub 7
	JGTZ SWAP
	Jump NO_SWAP
SWAP: Load 6
	Store *4	; a[j] := a[j-1]
	Load 7
	Store *5	; a[j-1] := a[j]
NO_SWAP: Load 3
	Sub =1
	Store 3	    ; j := j-1
	Jump INNER
NEXT_I: Load 2
	Add =1
	Store 2	    ; i := i+1
	Jump OUTER
PRINT_INIT: Load =1
	Store 8
PRINT_LOOP: Load 8
	Sub 1
	JGTZ END
	Load 8
	Add =9
	Store 9
	Write *9
	Load 8
	Add =1
	Store 8
	Jump PRINT_LOOP
END: Halt 0
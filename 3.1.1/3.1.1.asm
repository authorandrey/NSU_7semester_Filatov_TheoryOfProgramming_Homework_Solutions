;include Irvine32.inc
;include msvcrt.inc
;includelib ...
;.data
;	fmt_out db "%d", 10, 0
;.code
;Main PROC uses ebx esi edi
;	call ReadInt
;	mov ebx, eax	; l
;	call ReadInt
;	mov esi, eax	; r
;	call ReadInt
;	mov edi, eax	; s
;
;	.IF edi == 0
;		ret
;	.ENDIF
;	
;	.WHILE SDWORD ptr esi >= SDWORD ptr ebx
;		invoke crt_printf, addr fmt_out, ebx
;		add ebx, edi
;	.ENDW
;	ret
;Main ENDP
;start:
;	call Main
;	ret
;END

Read 1	; l
Read 2	; r
Read 3	; s

Load 3
JZero END

WHILE: Load 1
	Sub 2	; r0 := l + s*k - r, k - number of iteration
	JGTZ END
	Write 1 ; OUT <- r1 = l + s*k
	Load 3
	Add 1
	Store 1	; r1 := r1 + r3
	Jump WHILE
END: Halt 0
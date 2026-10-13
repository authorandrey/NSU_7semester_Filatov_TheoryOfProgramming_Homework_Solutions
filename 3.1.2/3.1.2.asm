;include Irvine32.inc
;include msvcrt.inc
;includelib ...
;.data
;	fmt_out db "%d", 10, 0
;.code
;Main PROC uses ebx esi edi
;	call ReadInt
;	mov esi, eax	; d
;	call ReadInt
;	mov edi, eax	; n
;	
;	.WHILE edi != 0
;		call ReadInt
;		mov ebx, eax
;		div esi
;		mul esi
;		sub ebx
;		.IF eax == 0
;			crt_printf addr fmt_out, ebx
;		.ENDIF
;		dec edi
;	.ENDW
;	ret
;Main ENDP
;start:
;	call Main
;	ret
;END

Read 2	; d
Read 3	; n

WHILE: Load 3
	JZero END
	Read 0
	Store 1	; r1 := a_n
	Div 2
	Mult 2
	Sub 1
	JZero WRITE
	Jump DEC_WHILE
WRITE: Write 1
DEC_WHILE: Load 3
	Sub =1
	Store 3	; r3--
	Jump WHILE
END: Halt 0
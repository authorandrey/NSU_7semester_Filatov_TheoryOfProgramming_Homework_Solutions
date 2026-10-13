;Main PROC
;	LOCAL buf: ptr DWORD
;
;	call ReadInt
;	mov ebx, eax	; n
;	
;	.IF ebx < 0
;		ret
;	.ENDIF
;	
;	invoke crt_malloc, ebx * 4
;	mov buf, eax
;	
;	mov esi, 0
;	.WHILE esi != ebx
;		call ReadInt
;		mov DWORD ptr [buf + esi * 4], eax
;		inc esi
;	.ENDW
;	
;	mov esi, 0
;	.WHILE esi != ebx
;		mov eax, [buf + esi * 4]
;		mov edx, [buf + ebx * 4]
;		.IF eax != edx
;			invoke crt_printf, addr fmt_out, 0
;			invoke crt_free, buf
;			ret
;		.ENDIF
;		inc esi
;		dec ebx
;	.ENDW
;	
;	invoke crt_printf, addr fmt_out, 1
;	invoke crt_free, buf
;	ret
;Main ENDP

Read 1	; n

Load =0
Sub 1
JGTZ SUCCESS	; n < 0
JZero SUCCESS	; n == 0

Load =3
Store 2		; buf starts at r3
Load 1
Add =3
Store 1		; buf ends at r{n+3} (not including last)
FILL_LOOP: Load 1
	Sub 2
	JZero END_FILL
	Read *2	; r{3+index} <- input
	Load 2
	Add =1
	Store 2	; inc r2
	Jump FILL_LOOP
END_FILL: Load =3
	Store 2	; restart start pointer
	Load 1
	Sub =1
	Store 1	; last element of buf is at r{n+3-1}
CHECK_LOOP: Load 1
	Sub 2
	JZero SUCCESS
	Load *1
	Sub *2
	JZero MOVE_INDEXES
	Jump FAIL
MOVE_INDEXES: Load 1
	Sub =1
	Store 1
	Load 2
	Add =1
	Store 2
SUCCESS: Write =1
	Halt 0
FAIL: Write =0
	Halt 0
	
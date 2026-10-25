; RASP-program loader
; In: n, A, args
; K = 218 loader registers. N = 2*n, B = max(N, K)+1, S = 179

; Pseudocode
; B := max(N, K)+1
; delta := B - S
; r211 := S
; r213 := B
; r215 := 26
; COPY:
;   copy this program from BODY to the end
; OFFSET:
;   shift all used registres of the copy to += delta
; BODY:
;   insert given program to r1...rN and jump to its start
; END

; Data Model
; V_N = r205            - registers that A take
; V_B = r207            - place from where to copy
; V_DELTA = r209        - offset of registers after copy
; V_SRC = r211          - ptr of initial loader register
; V_DST = r213          - ptr of copy register
; V_REMAIN = r215       - counter of remainig registers to copy
; V_PATCH = r217        - etc

START: Read 205                 ; r205 := n
    Load 205
    JGTZ N_POS
    Halt 0                      ; required n > 0
N_POS: Load 205
    Mult =2                     ; r205 = N := 2*n
    Store 205
    Load 205
    Sub =218
    JGTZ N_GREATER
    Load =219
    Store 207                   ; r207 = B := max(N, K)+1
    Jump BASE_READY
N_GREATER: Load 205
    Add =1
    Store 207                   ; r207 = B := max(N, K)+1
BASE_READY: Load 207
    Sub =179
    Store 209                   ; delta := B - S
    Load =179
    Store 211                   ; r211 := S
    Load 207
    Store 213                   ; r213 := B
    Load =26
    Store 215                   ; r215 := 26
; copy part of loader (after BODY_PTR)
COPY_LOOP: Load 215
    JZero COPY_DONE             ; exit if r215 == 0
    Load *211
    Store *213                  ; copy the register
    Load 211
    Add =1
    Store 211                   ; r211++ (next copy register)
    Load 213
    Add =1
    Store 213                   ; r213++ (next copy place)
    Load 215
    Sub =1
    Store 215                   ; 215-- (dec remaining)
    Jump COPY_LOOP
; shift BODY_LOOP copy
COPY_DONE: Load 207
    Add =5
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift JZero BODY_DONE
    Load 207
    Add =7
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift Read *180
    Load 207
    Add =9
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift Load 180
    Load 207
    Add =13
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift Store 180
    Load 207
    Add =15
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift Load 182
    Load 207
    Add =19
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift Store 182
    Load 207
    Add =21
    Store 217
    Load *217
    Add 209
    Store *217                  ; shift Jump BODY_LOOP
    Load 207
    Add =3
    Store 217                   ; r217 := B + 3
    Load 205
    Store *217                  ; ptr [B + 3] := N (Load =0 -> Load =N)
    Load 207
    Store 178                   ; Jump 1 -> Jump B
JUMP_COPY: Jump 1               ; Jump B
BODY_PTR: Load =1               ; memory: r179=Load, r180=1. r180 - address of writing given programm
BODY_LOOP: Load =0              ; Load =N
    JZero BODY_DONE
    Read *180                   ; Insert next register of inputted programm
    Load 180
    Add =1
    Store 180                   ; r180++
    Load 182
    Sub =1
    Store 182                   ; Load =N -> Load =N-1
    Jump BODY_LOOP
BODY_DONE: Load =0              ; r0 := 0
    Jump 1
    Halt 0 
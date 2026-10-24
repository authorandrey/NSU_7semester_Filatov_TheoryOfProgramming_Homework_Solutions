; Memory:
; 0  | 1 | 2 | ... | 15 | 16 |
; r0 |     programm_code     |

; Pseudocode:
; idx := 1              // idx lies after program code
; while idx <= 16 do
;     memory[idx] -> OUT
;     idx := idx + 1

Load =1         ; r0 := 1, pointer to the first cell of code

LOOP: Sub =16
    JGTZ END   ; if r0 > 16, then finish
    Add =16
    Write *0   ; output the value of the current cell
    Add =1     ; r0++
    Jump LOOP
END: Halt 0
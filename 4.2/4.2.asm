; Memory:
; 0  | 1 | 2 | ... | 21 | 22 | 23  |
; r0 |     programm_code     | idx |

; Pseudocode:
; idx := 1              // idx lies after program code
; while idx <= 22 do
;     memory[idx] -> OUT
;     idx := idx + 1

Load =1
Store 23       ; r23 := 1, pointer to the first cell of code

LOOP: Load 23
    Sub =22
    JGTZ END   ; if r23 > 22, then finish
    Write *23  ; output the value of the current cell
    Load 23
    Add =1
    Store 23   ; r23++
    Jump LOOP
END: Halt 0
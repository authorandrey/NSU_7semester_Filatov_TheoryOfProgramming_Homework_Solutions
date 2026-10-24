; RASP self-modification example.
; Store 7 changes the opcode of the next-to-last Write from 20 to 0 (Halt).
; The Jump skips that modified instruction and continues at CONTINUE.
Load =0
Store 7
Jump CONTINUE
Write =99
CONTINUE: Write =42
Halt 0

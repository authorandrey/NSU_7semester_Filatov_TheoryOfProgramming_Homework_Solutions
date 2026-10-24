Read 1  ; shift
Load =0
Sub 1
JZero SHIFT         ; if shift == 0 then do not write preamble
JGTZ NULLIFY_SHIFT  ; shift < 0 is invalid, therefore shift := 0
Jump WRITE_PREAMBLE

NULLIFY_SHIFT: Load =0
    Store 1
WRITE_PREAMBLE: Write =23
    Load 1
    Add =1
    Write 0         ; Jump shift+1 -> OUT
    Load 1
    Sub =1          ; r0 := shift - 1
WRITE_PREAMBLE_HALTS: JZero SHIFT
    Write =0
    Write =0        ; Halt 0 -> OUT
    Sub =1
    Jump WRITE_PREAMBLE_HALTS
SHIFT: Read 2
    Load =0
    Sub 2
    JZero END
    JGTZ END        ; if n <= 0 then end program
SHIFT_CYCLE: Load 2
    JZero END
    Read 3
    Read 4          ; r3 := instruction opcode, r4 := argument
    Load 3
    Sub =22
    JGTZ MAKE_SHIFT
    Jump PRINT      ; if opcode >= 23 then instruction is Jump|JZero|JGTZ
MAKE_SHIFT: Load 4
    Add 1
    Store 4         ; argument += shift
    Jump PRINT
PRINT: Write 3
    Write 4         ; opcode -> OUT, arg(maybe shifted) -> OUT
    Load 2
    Sub =1
    Store 2         ; n--
    Jump SHIFT_CYCLE
END: Halt 0
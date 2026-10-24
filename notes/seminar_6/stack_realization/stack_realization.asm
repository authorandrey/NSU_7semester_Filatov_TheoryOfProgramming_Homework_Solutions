Load =4 ; initialize stack pointer
Store 3 ; reserved pointer cell
Jump 4 ; skip initialization
__STACKGEN_ENTRY: Jump 5
__STACKGEN_BODY: Jump 6 ; label alias
__STACKGEN_SRC_1: Jump 7 ; label alias
LOAD: Read 0
__STACKGEN_SRC_2: JZero 19 ; if a_i == 0 then array is ended
__STACKGEN_SRC_3: Load 0 ; push 0
Store *3 ; write at stack top
Load 3
Add =1
Store 3 ; SP := SP + 1
__STACKGEN_SRC_4: Load 1
__STACKGEN_SRC_5: Add =1
__STACKGEN_SRC_6: Store 1 ; r1++
__STACKGEN_SRC_7: Jump 7
__STACKGEN_SRC_8: Jump 19 ; label alias
PRINT: Load 1
__STACKGEN_SRC_9: JZero 32 ; if r1 == 0 then array is ended
__STACKGEN_SRC_10: Load 3 ; pop into 0
Sub =1
Store 3 ; SP := SP - 1
Load *3
Store 0
__STACKGEN_SRC_11: Write 0
__STACKGEN_SRC_12: Load 1
__STACKGEN_SRC_13: Sub =1
__STACKGEN_SRC_14: Store 1 ; r1--
__STACKGEN_SRC_15: Jump 19
__STACKGEN_SRC_16: Jump 32 ; label alias
END: Halt 0

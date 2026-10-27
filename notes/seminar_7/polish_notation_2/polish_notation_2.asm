; def evaluate():
;     expression = []
;     while True:
;         token = read()
;         if token == 0:
;             break
;         expression.append(token)
;     values = {}
;     while True:
;         code = read()
;         if code == 0:
;             break
;         values[code] = read()
;     stack = []
;     for token in expression:
;         if token > 0:
;             stack.append(token)
;         elif token in (-5, -6, -7):
;             stack.append(values[token])
;         else:
;             right = stack.pop()
;             left = stack.pop()
;             if token == -1: result = left + right
;             elif token == -2: result = left - right
;             elif token == -3: result = left * right
;             elif token == -4:
;                 if right == 0: while True: pass
;                 result = left / right
;             stack.append(result)
;     write(stack.pop())

; Data Model
; 0: r0
; 1: next free expression cell
; 2: current token
; 3: sp
; 4: variable code | right operand
; 5: value | left operand
; 6: current expression token
; 7: end
; 20: x
; 21: y
; 22: z
; 1000...1999: expression
; 2000...: stack

Load =1000
Store 1                 ; r1 = 1000, start of expression stack

READ_EXPR: Read 2
	Load 2
	JZero END_EXPR
	Load 2
	Store *1               ; *r1 = token
	Load 1
	Add =1
	Store 1                ; expression pointer ++
	Jump READ_EXPR
; Save the address immediately after the expression.
END_EXPR: Load 1
	Store 7                ; r7 = end address of expression
; Read the variable table as (code, value) pairs until code 0.
READ_TABLE: Read 4
	Load 4
	JZero START_EVAL
	Read 5
	Load 4
	Add =5
	JZero SAVE_X
	Load 4
	Add =6
	JZero SAVE_Y
	Load 4
	Add =7
	JZero SAVE_Z
	Jump INVALID           ; unknown variable
SAVE_X: Load 5
	Store 20               ; r20 = x
	Jump READ_TABLE
SAVE_Y: Load 5
	Store 21               ; r21 = y
	Jump READ_TABLE
SAVE_Z: Load 5
	Store 22               ; r22 = z
	Jump READ_TABLE
START_EVAL: Load =1000
	Store 6                ; r6 = first expression token
	Load =2000
	Store 3                ; r3 = next free stack cell
EVAL_LOOP: Load 6
	Sub 7
	JZero EVAL_DONE         ; stop if r6 = end address
	Load *6
	Store 2                 ; r2 = current token
	Load 6
	Add =1
	Store 6                 ; next token
	Load 2
	JGTZ PUSH_CONST         ; push the number
	Load 2
	Add =5
	JZero PUSH_X            ; push x
	Load 2
	Add =6
	JZero PUSH_Y            ; push y
	Load 2
	Add =7
	JZero PUSH_Z            ; push z
    ; If code if from -1 to -4 then it is operator
	Load 2
	Add =1
	JZero OPERATOR         
	Load 2
	Add =2
	JZero OPERATOR
	Load 2
	Add =3
	JZero OPERATOR
	Load 2
	Add =4
	JZero OPERATOR
	Jump INVALID
PUSH_CONST: Load 2
	Jump PUSH_VALUE
PUSH_X: Load 20
	Jump PUSH_VALUE
PUSH_Y: Load 21
	Jump PUSH_VALUE
PUSH_Z: Load 22
	Jump PUSH_VALUE
; Push r0
PUSH_VALUE: Store *3
	Load 3
	Add =1
	Store 3                 ; sp++
	Jump EVAL_LOOP
OPERATOR: Load 3
	Sub =1
	Store 3
	Load *3
	Store 4                 ; r4 = right operand
	Load 3
	Sub =1
	Store 3
	Load *3
	Store 5                 ; r5 = left operand
	Load 2
	Add =1
	JZero DO_ADD            ; +
	Load 2
	Add =2
	JZero DO_SUB            ; -
	Load 2
	Add =3
	JZero DO_MULT           ; *
	Load 2
	Add =4
	JZero DO_DIV            ; /
	Jump INVALID
DO_ADD: Load 5
	Add 4
	Jump PUSH_VALUE         ; push left + right
DO_SUB: Load 5
	Sub 4
	Jump PUSH_VALUE         ; push left - right
DO_MULT: Load 5
	Mult 4
	Jump PUSH_VALUE         ; push left * right
DO_DIV: Load 4
	JZero DIV_ZERO          ; division by zero is invalid
	Load 5
	Div 4
	Jump PUSH_VALUE         ; push left / right
; The final stack element is the expression result
EVAL_DONE: Load 3
	Sub =1
	Store 3
	Write *3
	Halt 0
DIV_ZERO: Jump DIV_ZERO
INVALID: Jump INVALID
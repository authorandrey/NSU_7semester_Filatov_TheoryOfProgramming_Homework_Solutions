;def evaluate():
;    stack = []
;    while True:
;        x = read()
;        if x == 0:
;            break
;        if x > 0:
;            stack.append(x)
;            continue
;        right = stack.pop()
;        left = stack.pop()
;        if x == -1:
;            result = left + right
;        elif x == -2:
;            result = left - right
;        elif x == -3:
;            result = left * right
;        elif x == -4:
;            if right == 0:
;                while True:
;                    pass
;            result = left / right
;        stack.append(result)
;    write(stack.pop())

Load =1000
Store 1                 ; sp = 1000

READ_TOKEN: Read 2
    Load 2
    JZero FINISH
    JGTZ PUSH            ; num > 0 ==> push
POP_OPERANDS: Load 1
    Sub =1
    Store 3              ; ptr = sp - 1
    Load *3
    Store 4              ; right = top element
    Load 1
    Sub =1
    Store 1              ; sp--
    Load 1
    Sub =1
    Store 3
    Load *3
    Store 5              ; left = next element
    Load 1
    Sub =1
    Store 1              ; sp--
    Load 2
    Add =1
    JZero OP_ADD         ; -1: add
    Load 2
    Add =2
    JZero OP_SUB         ; -2: sub
    Load 2
    Add =3
    JZero OP_MULT        ; -3: mult
    Load 2
    Add =4
    JZero OP_DIV         ; -4: div
    Jump INVALID
OP_ADD: Load 5
    Add 4
    Jump PUSH_RESULT
OP_SUB: Load 5
    Sub 4
    Jump PUSH_RESULT
OP_MULT: Load 5
    Mult 4
    Jump PUSH_RESULT
OP_DIV: Load 4
    JZero DIV_ZERO       ; division by zero error
    Load 5
    Div 4
    Jump PUSH_RESULT
PUSH_RESULT: Store *3    ; stack[sp] = result
    Load 1
    Add =1
    Store 1              ; sp++
    Jump READ_TOKEN
PUSH: Load 1
    Store 3              ; ptr = sp
    Load 2
    Store *3             ; stack[sp] = num
    Load 1
    Add =1
    Store 1              ; sp++
    Jump READ_TOKEN
FINISH: Load 1
    Sub =1
    Store 3              ; ptr = sp - 1
    Write *3
    Halt 0
DIV_ZERO:   Jump DIV_ZERO
INVALID:    Jump INVALID
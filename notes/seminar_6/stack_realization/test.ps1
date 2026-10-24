py ..\..\..\ram_stack_machine_translator\ram_stack_translator.py .\stack_realization.ram_stack --stack-base 4
java -jar ..\..\..\ram-machine-emulator.jar .\stack_realization.asm
java -jar ..\..\..\ram-machine-emulator.jar .\stack_realization.bin "1 2 3 0" 1000
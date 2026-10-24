py ..\..\..\ram_call_machine_translator\call_translator.py .\map_sum.tur_call --stack-base 100
java -jar ..\..\..\ram-machine-emulator.jar .\map_sum.asm
java -jar ..\..\..\ram-machine-emulator.jar .\map_sum.bin "3 2 1 1 2 2 3 3" 100
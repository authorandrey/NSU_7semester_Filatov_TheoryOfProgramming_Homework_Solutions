# rasp-machine-emulator
Simple emulator of RAM machines. Intended to be used as supplementary material to "Theory of programming" course in Novosibirsk State University (see https://github.com/Svazars/theory-of-programming-notes).


## How to use

- Ensure `java` is installed on your computer (e.g. `java -version` should print something).
- Download latest stable release (https://github.com/Svazars/ram-machine-emulator/releases/) or build emulator from sources.
- Unzip release archive.
- `cd samples/Printer` and run `run.sh`. You should see successful emulation of simple tutorial program.
- Use `java -jar rasp-machine-emulator.jar` to get list of available options.

Now you could play around with other samples and start writing your own programs for RAM machines!

## How to develop

This section is under construction :)


## RASP mode

The emulator also supports RASP programs, where the instructions and data share the
same memory. The compiled program is loaded into memory cells `1, 2, ...`: each
instruction occupies two cells (`opcode`, `argument`), and execution starts at cell
`1`. A normal instruction advances the program counter by two; jump arguments are
absolute memory addresses of opcode cells. Since code and data share memory,
`Store` and `Read` can modify instruction opcodes or arguments.

Examples:

- `java -jar rasp-machine-emulator.jar --compile-rasp samples/RASP/Jump.asm` -- compile an
  assembly file with RASP label addresses (labels resolve to `1, 3, 5, ...`).
- `java -jar rasp-machine-emulator.jar --rasp samples/RASP/Jump.bin "" 1000` -- run a RASP
  program with no input.
- `java -jar rasp-machine-emulator.jar --rasp-test samples/RASP/Jump.bin samples/RASP/Jump.tests 1000`
  -- test a RASP program.

The original commands without the `--rasp` option retain their RAM semantics.

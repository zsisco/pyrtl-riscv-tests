# Processor development in PyRTL

- `single_cycle.py` is a PyRTL design for a single-cycle implementation of a subset of the RISC-V ISA.
  It only implements `add`, `addi`, `lw`, `jalr`, and `beq` from the RV32I ISA.
- `test_cpu.py` is a test bench program that loads the PyRTL design in `single_cycle.py` and tests a couple short programs.
  Pass the `--debug` argument for more detailed simulation info.
- `program.py` defines a class for loading RISC-V programs for testing. Probably don't need to edit this.


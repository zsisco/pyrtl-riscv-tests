import pyrtl, sys
from argparse import ArgumentParser
from enum import IntEnum
from program import Program
from single_cycle import single_cycle_cpu

# Add more tests here:
benchmarks = [
    # Test add functionality
    Program(
        name="add",
        instructions=[
            0x00100313, # addi x6, x0, 1
            0x00200393, # addi x7, x0, 2
            0x007302b3, # add x5, x6, x7
        ],
        rf={
            5: 3,
            6: 1,
            7: 2,
        },
        dmem={},
    ),
    # Test that the zero register is not changed throughout program execution
    Program(
        name="zero",
        instructions=[
            # main:
            0x00000533,  # add x10, x0, x0     # zero is initially set to 0 so a0 = 0.
            0x00402003,  # lw x0, 1(x0)        # this line shoudn't change zero
            0x00500413,  # addi x8, x0, 5      # s0 = 5
            0x00240013,  # addi zero, s0, 0x2  # This line also shoudn't change zero
            # exit:
        ],
        rf={8: 5, 10: 0},
        dmem={},
    ),]

if __name__ == "__main__":
    parser = ArgumentParser("Test the RISC-V cpu implementation.")
    parser.add_argument(
        "--debug", action="store_true", help="display memory on each cycle"
    )
    args = parser.parse_args()

    # Load the design
    single_cycle_cpu()

    # Execute each benchmark
    for program in benchmarks:
        program.execute(debug=args.debug)

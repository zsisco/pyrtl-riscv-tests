import pyrtl

def control(op):
    alu_imm = pyrtl.WireVector(bitwidth=1)
    write_reg = pyrtl.WireVector(bitwidth=1)
    read_mem = pyrtl.WireVector(bitwidth=1)
    jump = pyrtl.WireVector(bitwidth=1)
    branch = pyrtl.WireVector(bitwidth=1)

    with pyrtl.conditional_assignment(
            defaults={
                alu_imm: 0,
                write_reg: 0,
                read_mem: 0,
                jump: 0,
                branch: 0,
            }
    ):
        with op == 0b0110011: # ADD
            alu_imm |= 0
            write_reg |= 1
            read_mem |= 0
            jump |= 0
            branch |= 0
        with op == 0b0010011: # ADDI
            alu_imm |= 1
            write_reg |= 1
            read_mem |= 0
            jump |= 0
            branch |= 0
        with op == 0b0000011: # LW
            alu_imm |= 1
            write_reg |= 1
            read_mem |= 1
            jump |= 0
            branch |= 0
        with op == 0b1100111: # JALR
            alu_imm |= 1
            write_reg |= 1
            read_mem |= 0
            jump |= 1
            branch |= 0
        with op == 0b1100011: # BEQ
            alu_imm |= 0
            write_reg |= 0
            read_mem |= 0
            jump |= 0
            branch |= 1

    return (alu_imm, write_reg, read_mem, jump, branch)

def single_cycle_cpu():
    # --- Fetch (IF) ---
    pc = pyrtl.Register(bitwidth=32, name='pc')
    imem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name="imem", asynchronous=True)

    pc4 = pyrtl.WireVector(bitwidth=32, name="pc4")
    pc4 <<= pc + 4

    branch_taken = pyrtl.WireVector(bitwidth=1)
    branch_target = pyrtl.WireVector(bitwidth=32)

    with pyrtl.conditional_assignment:
        with branch_taken:
            pc.next |= branch_target
        with pyrtl.otherwise:
            pc.next |= pc4

    inst = pyrtl.WireVector(bitwidth=32, name="inst")
    inst <<= imem[pyrtl.shift_right_logical(pc, 2)]

    # --- Decode (ID) ---
    opcode = pyrtl.WireVector(bitwidth=7, name='opcode')
    rd = pyrtl.WireVector(bitwidth=5, name='rd')
    rs1 = pyrtl.WireVector(bitwidth=5, name='rs1')
    rs2 = pyrtl.WireVector(bitwidth=5, name='rs2')
    imm = pyrtl.WireVector(bitwidth=32, name='imm')

    opcode <<= inst[:7]

    # control logic
    (
        ctrl_alu_imm,
        ctrl_write_reg,
        ctrl_read_mem,
        ctrl_jump,
        ctrl_branch
       ) = control(opcode)

    rd <<= inst[7:12]
    rs1 <<= inst[15:20]
    rs2 <<= inst[20:25]

    imm <<= pyrtl.select(
        ctrl_branch,
        pyrtl.concat(
            inst[31], inst[7], inst[25:31], inst[8:12], 0
        ).sign_extended(32),
        inst[20:].sign_extended(32))

    rf = pyrtl.MemBlock(bitwidth=32, addrwidth=5, name="rf", asynchronous=True)

    rs1_val = pyrtl.WireVector(bitwidth=32, name="rs1_val")
    rs2_val = pyrtl.WireVector(bitwidth=32, name="rs2_val")

    rs1_val <<= pyrtl.select(
        rs1 == 0,
        pyrtl.Const(0, bitwidth=32),
        rf[rs1])

    rs2_val <<= pyrtl.select(
        rs2 == 0,
        pyrtl.Const(0, bitwidth=32),
        rf[rs2])

    # --- Execute ---
    alu_out = pyrtl.WireVector(bitwidth=32, name='alu_out')
    alu_out <<= pyrtl.select(
        ctrl_branch,
        rs1_val ^ rs2_val,
        pyrtl.select(
            ctrl_alu_imm,
            rs1_val + imm,
            rs1_val + rs2_val))

    branch_taken <<= ctrl_jump | (ctrl_branch & (alu_out == 0))
    branch_target <<= pyrtl.select(
        ctrl_branch,
        pc + imm,
        alu_out)

    # data memory, read
    dmem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name="dmem", asynchronous=True)
    read_data = pyrtl.WireVector(bitwidth=32, name='read_data')
    read_addr = pyrtl.shift_right_arithmetic(alu_out, 2)
    read_data <<= dmem[read_addr]

    reg_write_data = pyrtl.WireVector(bitwidth=32, name="reg_write_data")
    reg_write_data <<= pyrtl.select(
        ctrl_read_mem,
        read_data,
        pyrtl.select(
            ctrl_jump,
            pc4,
            alu_out))

    # --- Write Back (WB) ---
    rf[rd] <<= pyrtl.MemBlock.EnabledWrite(
        reg_write_data,
        (ctrl_write_reg | ctrl_read_mem) & (rd != 0))

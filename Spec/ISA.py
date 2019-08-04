"""
This module defines the instruction set architecture (ISA)
of the processor
"""

# Halt clock
# The Processor can only leave this state by resetting
HLT = 1 << 0x0

# Memory address register in
# Latch the current state of the databus into the Memory address register (MAR)
MI = 1 << 0x1

# RAM data out
# Put the currently selected RAM byte onto the databus
RO = 1 << 0x2

# RAM data in
# Write the current state of the databus into the active RAM byte
RI = 1 << 0x3

# Instruction register out
# Put the lower nibble (the data section) of the instruction register (IR)
# onto the databus. The upper nibble will always read as 0
IO = 1 << 0x4

# Instruction register in
# Write the current state of the databus into the IR
II = 1 << 0x5

# A register out
# Put the content of the register A (RA) onto the databus
AO = 1 << 0x6

# A register in
# Latch the current state of the databus into RA
AI = 1 << 0x7

# ALU out
# Put the sum of register A and B onto the databus
EO = 1 << 0x8

# ALU subtract
# compute RA - RB instead of the sum
SU = 1 << 0x9

# B register in
# Latch the current state of the databus into register B (RB)
BI = 1 << 0xA

# Output register in
# Latch the current state of the databus into the output register (OUT)
# This will cause the 7-segment display to display the current value of
# the databus until a new byte is latched into this register
OI = 1 << 0xB

# Program counter enable
# Increment the program counter on the next clock-cycle
CE = 1 << 0xC

# Program counter out
# Put the current program counter (PC) value the databus. Only the lower
# nibble will ever read as non-zero
CO = 1 << 0xD

# Jump (program counter in)
# Latch the current state of the databus into the PC
JP = 1 << 0xE

# Flags in
# latch the current state of the flags (ZF and CF) into the flags register (FR)
FI = 1 << 0xF

# a fetch cycle takes the first 2 microinstructions of every instruction
# 1. the current PC value is loaded into the MAR
# 2. a) the content of the RAM at this address is latched into the IR
# 2. b) The PC is advanced to the next instruction
FETCH_CYCLE = [CO | MI, RO | II | CE]

# an empty control word does not modify the state of the processor during
# a microinstruction and is thus a noop
NOP = 0x00

# this maps all instructions (by their mnemonic) to the 5 microinstructions that are
# executed during the instruction. Each instruction is enumerated by a 4-bit value, the
# upper nibble of the opcode and can contain a 4-bit value (instruction data, ID) in the
# lower nibble
MICROCODE = {
    # A no op (NOP) does nothing but a fetch cycle, thus simply advances to the next instruction
    "NOP": FETCH_CYCLE + [],
    # Load the value of the RAM at the address specified by the ID of the instruction into RA
    #
    # 1. Load the lower nibble of the IR into the MAR
    # 2. Load the selected RAM byte into RA
    "LDA": FETCH_CYCLE + [IO | MI, RO | AI],
    # Calculate the sum of the value of the RAM value specified by
    # the ID of the instruction and RA and store the result in RA
    #
    # 1. Load the lower nibble of the IR into the MAR
    # 2. Load the selected RAM byte into RB
    # 3. a) Take the output of the ALU and store it in register A
    # 3. b) Save the state of the flags into the FR
    "ADD": FETCH_CYCLE + [IO | MI, RO | BI, EO | AI | FI],
    # Calculate the difference of the value of the RAM value specified by
    # the ID of the instruction and RA and store the result in RA
    #
    # 1. Load the lower nibble of the IR into the MAR
    # 2. Load the selected RAM byte into RB
    # 3. a) Set the SU control bit to make the ALU output the difference
    #   rather than the sum between RA and RB
    # 3. b) Take the output of the ALU and store it in register A
    # 3. c) Save the state of the flags into the FR
    "SUB": FETCH_CYCLE + [IO | MI, RO | BI, SU | EO | AI | FI],
    # Store the contents of RA into the RAM cell specified by the ID of the instruction
    #
    # 1. Load the ID into the MAR
    # 2. Store the content of RA into RAM
    "STA": FETCH_CYCLE + [IO | MI, AO | RI],
    # Load data immediatley into RA
    #
    # 1. Store the ID of the instruction into RA
    "LDI": FETCH_CYCLE + [IO | AI],
    # Jump to another instruction (set the PC to the instructions ID)
    #
    # 1. Set the PC to the ID of the instruction
    "JMP": FETCH_CYCLE + [IO | JP],
    # Jump to another instruction if the carry flag is set
    # this has the same microinstruction steps as a normal JMP
    # but will be overwritten as NOP in cases where the flag is
    # not set (address bit FLAG_CF (A9) is cleared)
    "JC": FETCH_CYCLE + [IO | JP],
    # Jump to another instruction if the zero flag is set
    # this has the same microinstruction steps as a normal JMP
    # but will be overwritten as NOP in cases where the flag is
    # not set (address bit FLAG_ZF (A8) is cleared)
    "JZ": FETCH_CYCLE + [IO | JP],
    # Set the output display to show the current contents of RA
    #
    # 1. Latch the current value of RA into the OUT register
    "OUT": FETCH_CYCLE + [AO | OI],
    # Halt all further program execution. Although this will also run
    # a fetch cycle and thus advance the PC, the next instruction will
    # never be executed
    #
    # 1. hHlt the clock
    "HLT": FETCH_CYCLE + [HLT],
}

# maps numeric opcodes to their mnemonic name
OPCODES = {
    0x0: "NOP",
    0x1: "LDA",
    0x2: "ADD",
    0x3: "SUB",
    0x4: "STA",
    0x5: "LDI",
    0x6: "JMP",
    0x7: "JC",
    0x8: "JZ",
    0x9: "NOP",
    0xA: "NOP",
    0xB: "NOP",
    0xC: "NOP",
    0xD: "NOP",
    0xE: "OUT",
    0xF: "HLT",
}

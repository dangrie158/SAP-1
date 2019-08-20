"""
This module defines the instruction set architecture (ISA)
of the processor
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Sequence

# an empty control word does not modify the state of the processor during
# a microinstruction and is thus a noop
CW_NOP = 0x00


class CW(IntEnum):

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


@dataclass
class Instruction:
    """
    this maps all instructions (by their mnemonic) to the 5 microinstructions that are
    executed during the instruction. Each instruction is enumerated by a 4-bit value, the
    upper nibble of the opcode and can contain a 4-bit value (instruction data, ID) in the
    lower nibble
    """

    name: str
    microcode: Sequence[CW]
    opcode: int
    has_parameter: bool

class MetaInstructionSet(type):
    @property
    def set(cls):
        return {k: i for k, i in cls.__dict__.items() if isinstance(i, Instruction)}

    @property
    def instructions(cls):
        return [i for i in cls.__dict__.values() if isinstance(i, Instruction)]

    @property
    def __getitem__(cls, key):
        return cls.set[key]

class InstructionSet(dict, metaclass=MetaInstructionSet):
    @classmethod
    def by_opcode(cls, opcode):
        return next((i for i in cls.instructions if i.opcode == opcode), cls.NOP)

    @classmethod
    def instructions_with_parameter(cls, opcode):
        return next((i for k, i in cls if i.opcode == opcode), cls.NOP)


# a fetch cycle takes the first 2 microinstructions of every instruction
# 1. the current PC value is loaded into the MAR
# 2. a) the content of the RAM at this address is latched into the IR
# 2. b) The PC is advanced to the next instruction
InstructionSet.FETCH_CYCLE = [CW.CO | CW.MI, CW.RO | CW.II | CW.CE]

# A no op (NOP) does nothing but a fetch cycle, thus simply advances to the next instruction
InstructionSet.NOP = Instruction("NOP", InstructionSet.FETCH_CYCLE + [], 0x0, False)
# Load the value of the RAM at the address specified by the ID of the instruction into RA
#
# 1. Load the lower nibble of the IR into the MAR
# 2. Load the selected RAM byte into RA

InstructionSet.LDA = Instruction(
    "LDA", InstructionSet.FETCH_CYCLE + [CW.IO | CW.MI, CW.RO | CW.AI], 0x01, True
)

# Calculate the sum of the value of the RAM value specified by
# the ID of the instruction and RA and store the result in RA
#
# 1. Load the lower nibble of the IR into the MAR
# 2. Load the selected RAM byte into RB
# 3. a) Take the output of the ALU and store it in register A
# 3. b) Save the state of the flags into the FR
InstructionSet.ADD = Instruction(
    "ADD",
    InstructionSet.FETCH_CYCLE + [CW.IO | CW.MI, CW.RO | CW.BI, CW.EO | CW.AI | CW.FI],
    0x02,
    True,
)

# Calculate the difference of the value of the RAM value specified by
# the ID of the instruction and RA and store the result in RA
#
# 1. Load the lower nibble of the IR into the MAR
# 2. Load the selected RAM byte into RB
# 3. a) Set the SU control bit to make the ALU output the difference
#   rather than the sum between RA and RB
# 3. b) Take the output of the ALU and store it in register A
# 3. c) Save the state of the flags into the FR
InstructionSet.SUB = Instruction(
    "SUB",
    InstructionSet.FETCH_CYCLE
    + [CW.IO | CW.MI, CW.RO | CW.BI, CW.SU | CW.EO | CW.AI | CW.FI],
    0x03,
    True,
)

# Store the contents of RA into the RAM cell specified by the ID of the instruction
#
# 1. Load the ID into the MAR
# 2. Store the content of RA into RAM
InstructionSet.STA = Instruction(
    "STA", InstructionSet.FETCH_CYCLE + [CW.IO | CW.MI, CW.AO | CW.RI], 0x04, True
)

# Load data immediatley into RA
#
# 1. Store the ID of the instruction into RA
InstructionSet.LDI = Instruction(
    "LDI", InstructionSet.FETCH_CYCLE + [CW.IO | CW.AI], 0x05, True
)

# Jump to another instruction (set the PC to the instructions ID)
#
# 1. Set the PC to the ID of the instruction
InstructionSet.JMP = Instruction(
    "JMP", InstructionSet.FETCH_CYCLE + [CW.IO | CW.JP], 0x06, True
)

# Jump to another instruction if the carry flag is set
# this has the same microinstruction steps as a normal JMP
# but will be overwritten as NOP in cases where the flag is
# not set (address bit FLAG_CF (A9) is cleared)
InstructionSet.JC = Instruction(
    "JC", InstructionSet.FETCH_CYCLE + [CW.IO | CW.JP], 0x07, True
)

# Jump to another instruction if the zero flag is set
# this has the same microinstruction steps as a normal JMP
# but will be overwritten as NOP in cases where the flag is
# not set (address bit FLAG_ZF (A8) is cleared)
InstructionSet.JZ = Instruction(
    "JZ", InstructionSet.FETCH_CYCLE + [CW.IO | CW.JP], 0x08, True
)

# Set the output display to show the current contents of RA
#
# 1. Latch the current value of RA into the OUT register
InstructionSet.OUT = Instruction(
    "OUT", InstructionSet.FETCH_CYCLE + [CW.AO | CW.OI], 0x0E, False
)

# Halt all further program execution. Although this will also run
# a fetch cycle and thus advance the PC, the next instruction will
# never be executed
#
# 1. Halt the clock
InstructionSet.HLT = Instruction("HLT", InstructionSet.FETCH_CYCLE + [CW.HLT], 0xF, False)

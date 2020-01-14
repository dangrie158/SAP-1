"""
This module creates the microcode LUT decoder.
This lut will take

1. 3 bit microinstruction number (A0-A2)
2. an instruction nibble (A3 - A6)
3. a hardwired chip select (A7)
4. 2 bit flags (A8 - A9)

as input and translate it to a 16 bit control word.
To get the 16 bit, 2 8-bit EEPROMS are used, the first EEPROM
has its chip select tied low, while for the second chip
the line is always high. Thus the same LUT can be programmed 
into both EEPROMS
"""

from sys import stdout
import ISA

# first bit of the instruction in the address word
OPCODE_OFFSET = 3

# CS bit is low for the lower byte of the control word
CS_LOW_BYTE = 0 << 7
# CS bit is high for the higher byte
CS_HIG_BYTE = 1 << 7

# bit 8 of the address is the carry-flag
# this bit is set when the current ALU result overflows
# while the FI control bit is set
FLAG_CF = 1 << 8

# bit 9 of the address is the zero-flag
# this bit is set when the current ALU result is zero
# while the FI control bit is set
FLAG_ZF = 1 << 9

if __name__ == "__main__":
    # create a buffer for the eeprom memory with empty control words (NOP microinstructions)
    eeprom_content = bytearray([ISA.CW_NOP] * 2048)

    # iterate for all possible combination of flag bits
    for flags in [0x0, FLAG_ZF, FLAG_CF, FLAG_ZF | FLAG_CF]:
        # iterate over both chip select states
        for chip in [CS_LOW_BYTE, CS_HIG_BYTE]:
            # iterate over all possible opcodes
            for instruction_num in range(16):

                instruction = ISA.InstructionSet.by_opcode(instruction_num)
                mnemonic = instruction.name
                ucode = instruction.microcode
                opcode = instruction_num

                # iterate over all microsteps in this instruction
                for microstep, control_word in enumerate(ucode):

                    address = flags | chip | (opcode << OPCODE_OFFSET) | microstep

                    # select the upper or lower byte depending on the CS bit
                    cw_byte = (
                        control_word >> 8 if chip == CS_HIG_BYTE else control_word
                    ) & 0xFF

                    # mask the conditional jump ucodes after the fetchcycle depending on the flag state
                    if microstep >= len(ISA.InstructionSet.FETCH_CYCLE) and (
                        (mnemonic == "JC" and not FLAG_CF & flags)
                        or (mnemonic == "JZ" and not FLAG_ZF & flags)
                    ):
                        cw_byte = ISA.CW_NOP

                    eeprom_content[address] = cw_byte

    # write the lut to stdout
    stdout.buffer.write(eeprom_content)
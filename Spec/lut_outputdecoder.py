"""
This module will create a lookuptable to
decode a binary input byte to a 4-digit
7-segment display output.

2 modes are available positive and 2s-complement.

The byte to display is specified by the address 
pins A0-A7, A8 and A9 are the digit select pins and
A10 is used to select the output mode 

Segments are arranged as follows:
 ___
| a |
f   b
|-g-|
e   c
|_d_|  .DP
"""

import sys

SEG_A = 1 << 0
SEG_B = 1 << 1
SEG_C = 1 << 2
SEG_D = 1 << 3
SEG_E = 1 << 4
SEG_F = 1 << 5
SEG_G = 1 << 6
SEG_DP = 1 << 7

# all needed characters translated to the output of the LUT
CHARS = {
    '0': SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F,
    '1': SEG_B | SEG_C,
    '2': SEG_A | SEG_B | SEG_D | SEG_E | SEG_G,
    '3': SEG_A | SEG_B | SEG_C | SEG_D | SEG_G,
    '4': SEG_B | SEG_C | SEG_F | SEG_G,
    '5': SEG_A | SEG_C | SEG_D | SEG_F | SEG_G,
    '6': SEG_A | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G,
    '7': SEG_A | SEG_B | SEG_C,
    '8': SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G,
    '9': SEG_A | SEG_B | SEG_C | SEG_D | SEG_F | SEG_G,
    '-': SEG_G,
    '+': 0x00 # dont display anything
}

DIGITS = (
    # Digit 1 (LSB)
    0b00 << 8,
    # Digit 2
    0b01 << 8,
    # Digit 3
    0b10 << 8,
    # Digit 4 (MSB)
    0b11 << 8
)

MODE_NO = 0b0 << 10 # Normal Mode (positive ints in [0, 255])
MODE_2S = 0b1 << 10 # 2s complement (ints in [-128, 127])

def signed_to_unsigned(num):
    """
    Convert a signed 8-bit integer to a unsigned representation.
    No bits are changed, this just changes how the interpreter
    treats the object
    """
    byte_representation = num.to_bytes(1, sys.byteorder, signed=True)
    return int.from_bytes(byte_representation, sys.byteorder, signed=False)

if __name__ == '__main__':
    # create a buffer for the eeprom memory
    eeprom_content = bytearray(b'\x00' * 2048)

    # write the LUT for the normal mode
    for num in range(256):
        for digit in range(4):
            eeprom_content[num | DIGITS[digit] | MODE_NO] = CHARS[str((num // (10 ** digit)) % 10)]

    # write the LUT for the 2s-complement mode
    for num in range(-128, 128):
        for digit in range(3):
            eeprom_content[signed_to_unsigned(num) | DIGITS[digit] | MODE_2S] = CHARS[str((abs(num) // (10 ** digit)) % 10)]

        eeprom_content[num | DIGITS[3] | MODE_NO] = CHARS['-'] if num < 0 else CHARS['+']

    # write the lut to stdout
    sys.stdout.buffer.write(eeprom_content)
    
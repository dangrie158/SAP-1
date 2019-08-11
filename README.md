# SAP-1 (Simple as Possible)

A simple 8-bit micro-processor using mostly discrete logic chips.

This project is mostly based on the [8-bit Breadboard computer](https://eater.net/8bit) by [Ben Eater](https://eater.net)

## Banner Specs

- ~400 Hz Clock
- 8-bit Data Bus
- 16-bit Control Word
- 5 Microsteps per Instruction
- 16 byte RAM

## Documentation

Check the projects [Pages](https://dangrie158.github.io/SAP-1/) for the documentation of the ISA and Hardware modules.

## Submodules:

- Clock with adjustable frequency and single-step button
- 2 8-bit Data Registers (A & B)
- ALU implementing sum and difference between Registers A & B, carry and zero flag
- Flag Register to save the ALU flags between instructions
- 4-bit Instruction Counter with load (jump)
- Output module to display a byte as positive decimal or 2s-complement with data latch
- Random Access Memory with 16 Bytes for instructions and data
- 4-bit Memory Address Register to address the 16 bytes of RAM
- 8-bit Instruction Register with the upper nibble representing the opcode, the lower nibble can be used for instruction parameters
- Instruction Decoder to run the microcode of the 16 different instructions with 5 microinstuctions each. Uses a 16-bit control word to control the other modules

## Project Structure

| Files                           | Description                                                                                   |
|---------------------------------|-----------------------------------------------------------------------------------------------|
| ```Board/Board.*```             | Autodesk Eagle project woth the Schematic and a fully routed Boardlayout                      |
| ```Board/Board_*.zip```         | precreated Gerbers for Production                                                             |
| ```Board/BOM.xlsx```            | a BOM with [Mouser](https://www.mouser.com) partnumbers                                       |
| ```Spec/ISA.py```               | a Python module that defines and documents the Instruction Set Architecture of the Processor. |
| ```Spec/lut_microcode.py```     | script to create the microcode LUT binary for the ID EEPROMS. Uses ```ISA.py```               |
| ```Spec/lut_outputdecoder.py``` | script to create the LUT binary for the output decode EEPROM                                  |
| ```LUTs/*.bin```                | precreated binaries for the EEPROMS                                                           |
| ```Example-Programs/*.s```      | Some Example Programs in SAP-1 assembly                                                       |
| ```Tools/sap-asm```             | Assembler for SAP-1 assembly listings. Outputs binaries or prints programming instructions.   |
| ```Simulations/```              | [iCircuit](http://icircuitapp.com) simulation files for some parts of the architecture        |

## Writing Code
The documentation has an extensive section on the [Instruction Set Architecture](https://dangrie158.github.io/SAP-1/isa.html) you can use to get started writing programs.

### Assembler:

In the ``Tools`` directory an assembler is available that can either output binary files or, if it detects stdout to be a TTY, prints programming instructions for you to manually program the RAM using the DIP-Switches.

```
$ cat Example-Programs/Counter.s 
.data:
0xF: 0x1

LDA 0xF
loop:
OUT
ADD 0xF
JMP loop

$ Tools/sap-asm Example-Programs/Counter.s
○○○○: ○○○●●●●●
○○○●: ●●●○○○○○
○○●○: ○○●○●●●●
○○●●: ○●●○○○○●
●●●●: ○○○○○○○●

$ Tools/sap-asm Example-Programs/Counter.s | hexdump 
0000000 1f e0 2f 61 00 00 00 00 00 00 00 00 00 00 00 01
0000010
```


## Programming the EEPROM LUTs

The provided ```Makefile``` offers some convenient rules to create the LUTs and program them to an EEPROM.
To program the LUTs you can use an [Arduino based programmer](https://github.com/dangrie158/EEPROgraMmer)
with only 2 external chips (+EEPROM) which is the officially supported method using the 
[```eepro```](https://pypi.org/project/eepro/) CLI. 

However, you can also use any other programmer to flash the binary files created by the scripts.

If you want to use ```eepro```, make sure the package is installed

```bash
pip3 install -r requirements.txt
```

Then you can programm the needed 3 EEPROMS (1x Output Decoder, 2x Microcode) using 

```bash
make program_lut file=LUTs/microcode.bin        # < for the microcode EEPROMS
make program_lut file=LUTs/outputdecoder.bin    # < for the Output Decoder EEPROM
```

The rule makes sure the LUTs are created or updated if the creating script has changed since last creation.


If you want to use any other programmer, just run 

```bash
make luts
```

to create the binaries in the ```LUTs/``` directory.
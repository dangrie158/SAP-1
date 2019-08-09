==================================
Instruction Set Architecture (ISA)
==================================

Control Word
============
The **Control Word (CW)** consists of all the control lines of the
seperate modules described in the hardware section.
By driving these control lines, the behaviour of the modules can be controlled.
Most modules are synchronized with the clock, so a change in any of the control
bits will take effect on the next clock cycle. For example, driving the *AI*
line high will save whatever state the databus is in into Register A on the
next clock tick (and all further ticks until the control line is pulled low
again.
However, not all lines are syncronied with the clock, some will change the
module behaviour as soon as the line is changed. Generally, all input lines
are syncronized, while output lines will change immediately. This has the
nice side-effect that the databus will have the correct data on it before
the clock cycle latches this data into a module.

The control word is set by the **Instruction Decoder (ID)** which sets the
control lines between the clock ticks depending on the current instruction
and microinstruction. The CW consists of 16 control lines, thus is 16 bits
long.

The following table lists all control lines, their function and the position
they have in the CW. The final control word is thus created by ORing the values
in the CW column for all active control lines.

+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| CW     | Mnemonic | Name                     | Description                                                                   | Synced |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0001 |          |                          | Stop the main clock. This will also disable single-stepping                   | N      |
|        | HLT      | Halt Clock               | and the processor can only leave this state by resetting the                  |        |
|        |          |                          | system to clear the control word                                              |        |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0002 | MI       | Memory Address In        | Latch the current state of the databus into the Memory address register (MAR) | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0004 | RO       | RAM Out                  | Put the currently selected RAM byte onto the databus                          | N      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0008 | RI       | RAM In                   | Write the current state of the databus into the active RAM byte               | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0010 | IO       | Instruction Data Out     | Put the lower nibble (the data section) of the instruction register (IR)      | N      |
|        |          |                          | onto the databus. The upper nibble will always read as 0                      |        |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0020 | II       | Instruction Register In  | Write the current state of the databus into the IR                            | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0040 | AO       | Register A Out           | Put the content of the register A (RA) onto the databus                       | N      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0080 | AI       | Register A In            | Latch the current state of the databus into RA                                | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0100 | EO       | ALU Out                  | Put the sum of register A and B onto the databus                              | N      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0200 | SU       | ALU Substract            | compute RA - RB instead of the sum                                            | N      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0400 | BI       | Register B In            | Latch the current state of the databus into register B (RB)                   | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x0800 | OI       | Output Latch             | Latch the current state of the databus into the output register (OUT)         | Y      |
|        |          |                          | This will cause the 7-segment display to display the current value of         |        |
|        |          |                          | the databus until a new byte is latched into this register                    |        |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x1000 | CE       | Programcounter Enable    | Increment the program counter on the next clock-cycle                         | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x2000 | CO       | Programcounter Out       | Put the current program counter (PC) value the databus. Only the lower        | N      |
|        |          |                          | nibble will ever read as non-zero                                             |        |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x4000 | JP       | Jump (Programcounter In) | Latch the current state of the databus into the PC                            | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+
| 0x8000 | FI       | Store Flags              | Latch the current state of the flags (ZF and CF) into the flags register (FR) | Y      |
+--------+----------+--------------------------+-------------------------------------------------------------------------------+--------+

Microcode
=========
The Processor will run a list of instructions to execute a program.
Although individual instructions are on a pretty low level, they are
not quite atomic, since each instruction can consist of multiple
microinstructions.
The mapping from an instruction to a list of microinstructions is
called **microcode**.
Each Instruction can consist of up to 5 microinstructions (T0 - T4),
although this could easily be extended to 8 or even 16 steps
(as described in the hardware section).
However, since there is no way to advance to the next instruction
before the 5 microinstructions are all run, it makes sense to limit this
to only the maximum number of steps needed for any instruction.

During all microinstruction steps that are not needed, the CW is empty
(``0x0000``, all control lines are low).

Fetch Cycle
-----------
The first 2 microinstaructions are the same for all instructions and are
responsible to actually fetch the instruction from memory.
Thus only 3 microinstructions are effectivley available for the actual
instruction.

A fetch cycle consists of the following steps (microinstructions)

1. Drive the CO and MI lines high (CW:``0x2000 + 0x0002 = 0x2002``).
   This will load the current instruction's address into the MAR and
   thus the RAM module outputs the instruction as stored in memory.
2. Drive the RO, II and CE lines high
   (CW:``0x0004 + 0x0020 + 0x1000 = 0x1024``).
   This will load the instruction from RAM into the Instruction Register
   and also advance the Programcounter to point to the next instruction's
   address.

Instruction Table
-----------------
The following table shows the available instructions and the corresponding
microinstructions with the corresponding control lines that are driven high
to achieve the desired behaviour.
All unspecified control lines need to be driven low.

A instruction in the SAP-1 architecture consists of 1 byte. The upper nibble
of this byte (bits 4-7) are the opcode and identify the instruction. The lower
nibble (bits 0-3) can be used to pass parameters to the instruction (for
example a RAM Address).
This data is called **Instruction Data (ID)**.

As described earlier, not all insructions need the whole 5 microinstructions,
however since there is no way to reset the microinstruction counter in the
Instruction Decoder module, all instructions will need 5 clock cycles to
execute.
During the unused clock cycles, the CW is empty (``0x0000``).

+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| Opcode | Mnemonic | Function               | ID          | Description                                                       |    | CW         | Microinstruction Description                                     |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x0``|    NOP   | No-Op                  |             | A no op (NOP) does nothing but a fetch cycle, thus simply         |    |            |                                                                  |
|        |          |                        |             | advances to the next instruction                                  |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x1``|    LDA   | Load RA                | RAM Address | Load the value of the RAM at the address specified by the         | T2 | IO, MI     | Load the lower nibble of the IR into the MAR                     |
|        |          |                        |             | ID of the instruction into RA                                     +----+------------+------------------------------------------------------------------+
|        |          |                        |             |                                                                   | T3 | RO, AI     | Load the selected RAM byte into RA                               |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
|        |          | Caculate sum of data   | RAM Address | Calculate the sum of the value of the RAM value specified by,     | T2 | IO, MI     | Load the lower nibble of the IR into the MAR                     |
|        |          | and RA, store          |             | the ID of the instruction and RA and store the result in RA       +----+------------+------------------------------------------------------------------+
| ``0x2``|    ADD   | result in RA           |             |                                                                   | T3 | RO, BI     | Load the selected RAM byte into RB                               |
|        |          |                        |             |                                                                   +----+------------+------------------------------------------------------------------+
|        |          |                        |             |                                                                   | T4 | EO, AI, FI | a) Take the output of the ALU and store it in register A         |
|        |          |                        |             |                                                                   |    |            | b) Save the state of the flags into the FR                       |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x3``|    SUB   | Caculate difference of | RAM Address | Calculate the sum of the value of the RAM value specified by      | T2 | IO, MI     | Load the lower nibble of the IR into the MAR                     |
|        |          | data and RA, store     |             | the ID of the instruction and RA and store the result in RA       +----+------------+------------------------------------------------------------------+
|        |          | result in RA           |             |                                                                   | T3 | RO, BI     | Load the selected RAM byte into RB                               |
|        |          |                        |             |                                                                   +----+------------+------------------------------------------------------------------+
|        |          |                        |             |                                                                   | T4 | EO, AI, FI | a) Set the SU control bit to make the ALU output the difference, |
|        |          |                        |             |                                                                   |    |            | rather than the sum between RA and RB                            |
|        |          |                        |             |                                                                   |    |            | b) Take the output of the ALU and store it in RA                 |
|        |          |                        |             |                                                                   |    |            | c) Save the state of the flags into the FR                       |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x4``|    STA   | Store RA contents      | RAM Address | Store the contents of RA into the RAM cell specified by           | T2 | IO, MI     | Load the ID into the MAR                                         |
|        |          |                        |             | the ID of the instruction                                         +----+------------+------------------------------------------------------------------+
|        |          |                        |             |                                                                   | T3 | AO, RI     | Store the content of RA into RAM                                 |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x5``|    LDI   | Load immediately       | Data Nibble | Load data immediatley into RA                                     | T2 | IO, AI     | Store the ID of the instruction into RA                          |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x6``|    JMP   | Jump                   | RAM Address | Jump to another instruction (set the PC to the instructions ID)   | T2 | IO, JP     | Set the PC to the ID of the instruction                          |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x7``|    JC    | Jump if carry          | RAM Address | Jump to another instruction (set the PC to the instructions ID)   | T2 |            | NOP if the carry flag is not set                                 |
|        |          |                        |             | if the carry flag is currently set                                +----+------------+------------------------------------------------------------------+
|        |          |                        |             | (the last ALU computation did overflow)                           | T2 | IO, JP     | Set the PC to the ID of the instruction if the flag is set       |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x8``|    JZ    | Jump if zero           | RAM Address | Jump to another instruction (set the PC to the instructions ID)   | T2 |            | NOP if the zero flag is not set                                  |
|        |          |                        |             | if the zero flag is currently set                                 +----+------------+------------------------------------------------------------------+
|        |          |                        |             | (the last ALU computation resulted in a zero)                     | T2 | IO, JP     | Set the PC to the ID of the instruction if the flag is set       |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0x9``|          | *<unused>*             |             |                                                                   |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0xA``|          | *<unused>*             |             |                                                                   |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0xB``|          | *<unused>*             |             |                                                                   |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0xC``|          | *<unused>*             |             |                                                                   |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0xD``|          | *<unused>*             |             |                                                                   |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0xE``|    OUT   | Display contents of RA |             | Set the output display to show the current contents of RA         | T2 | AO, OI     | Latch the current value of RA into the OUT register              |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+
| ``0xF``|    HLT   | Halt the clock         |             | Halt all further program execution. Although this will also run,  | T2 | HLT        | Halt the clock                                                   |
|        |          |                        |             | a fetch cycle and thus advance the PC, the next instruction will, |    |            |                                                                  |
|        |          |                        |             | never be executed                                                 |    |            |                                                                  |
+--------+----------+------------------------+-------------+-------------------------------------------------------------------+----+------------+------------------------------------------------------------------+

The Microcode is implemented as a Lookuptable (LUT) in the EEPROMs of the
Instruction Decoder module.
See the files ``spec/ISA.py`` and ``spec/lut_microcode`` that will generate
the LUT for those EEPROMs. You can also create your own instructions with
your own microcode in the unused opcodes.

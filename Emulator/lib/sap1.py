import sys
import os

from .simulation import Clock, Signal, State, Junction, Bus
from .modules import *


# add the Spec directory to PYTHONPATH for importing the ISA
sys.path.append(os.path.join(os.path.dirname(__file__), "../../Spec"))
import ISA

simulation_clock = Clock(freq=5)

databus = Bus("Databus", width=8)
control_word = Bus(("Control Word", tuple(ISA.CW.__members__.keys())), width=16)

clk = Signal("CLK", State.LOW)
i_clk = Signal("!CLK", lambda: not clk)
clr = Signal("CLR", State.LOW)
i_clr = Signal("!CLR", lambda: not clr)

RA = DataRegister("RA", databus, clk, load=control_word['AI'], out=control_word['AO'], clr=clr)
RB = DataRegister("RB", databus, clk, load=control_word['BI'], out=Signal.VCC, clr=clr)
IR = InstructionRegister("IR", databus, clk, load=control_word['II'], out=control_word['IO'], clr=clr)
MAR = MemoryAddressRegister("MAR", databus, clk, load=control_word['MI'], clr=clr)
ALU = ALU(
    "ALU",
    databus,
    operand_1=RA.contents,
    operand_2=RB.contents,
    su=control_word['SU'],
    out=control_word['EO']
)
FR = FlagsRegister("FR", ALU.carry, ALU.zero, clk, load=control_word['FI'], clr=clr)
RAM = RAM("RAM", databus, MAR.address, clk, load=control_word['RI'], out=control_word['RO'])
PC = ProgramCounter("PC", databus, control_word['CE'], clk, control_word['JP'], i_clr, control_word['CO'])
ID = InstructionDecoder("ID", "LUTs/microcode.bin", control_word, IR.opcode, FR.CF, FR.ZF, i_clk, i_clr)
OUT = OutputDisplay("OUT", databus, clk, control_word['OI'], i_clr)

# print(bool(ALU.zero))
# BI.state = State.LOW
# AI.state = State.LOW
# val1 = State.HIGH
# val2 = State.LOW
# test = [Signal(initial= lambda: val1) for _ in range(4)] + [Signal(initial= lambda: val2) for _ in range(4)]

# databus.append(test)
# clk.toggle()
# clk.toggle()
# BI.state = State.HIGH
# AI.state = State.HIGH
# val1 = State.HIGH_Z
# val2 = State.HIGH_Z

# EO.state=State.LOW
# print(bool(ALU.zero))

# CO.state = State.LOW
# CE.state = State.HIGH

from pprint import pprint
@simulation_clock.every(simulation_clock.neg_edge)
@simulation_clock.every(simulation_clock.pos_edge)
def update():
    clk.toggle()
    clk.notify()
    i_clk.notify()

    print("-"*20)
    opcode_num = Bus.to_int(IR.opcode)
    print(f"Instruction {ISA.InstructionSet.by_opcode(opcode_num).name}")
    print(f"program counter {PC.counter.count}")
    print(f"memory address {Bus.to_int(MAR.address)}")
    print(f"RA contents {Bus.to_int(RA.contents)}")
    print(f"RB contents {Bus.to_int(RB.contents)}")
    print(f"Output contents {Bus.to_int(OUT.contents)}")



from .simulation import Clock, Signal, State, Junction, Bus
from .modules import *

simulation_clock = Clock(freq=1)

databus = Bus("Databus", width=8)
control_word = Bus("Control Word", width=16)

clk = Signal("CLK", State.LOW)
i_clk = Signal("!CLK", lambda: not clk)
clr = Signal("CLR", State.LOW)
i_clr = Signal("CLR", lambda: not clr)

AI = Signal("A In", State.HIGH)
AO = Signal("A Out", State.HIGH)

BI = Signal("B In", State.HIGH)

II = Signal("IR In", State.HIGH)
IO = Signal("IR Out", State.HIGH)

MI = Signal("MAR In", State.HIGH)

SU = Signal("ALU Substract", State.LOW)
EO = Signal("ALU Out", State.HIGH)

FI = Signal("Flags In", State.HIGH)

RO = Signal("RAM Out", State.HIGH)
RI = Signal("RAM In", State.HIGH)

CE = Signal("Counter Enable", State.LOW)
CI = Signal("Counter In", State.HIGH)
CO = Signal("Counter Out", State.HIGH)

RA = DataRegister("RA", databus, clk, load=AI, out=AO, clr=clr)
RB = DataRegister("RB", databus, clk, load=BI, out=Signal.VCC, clr=clr)
IR = InstructionRegister("IR", databus, clk, load=II, out=IO, clr=clr)
MAR = MemoryAddressRegister("MAR", databus, clk, load=MI, clr=clr)
ALU = ALU(
    "ALU",
    databus,
    operand_1=RA.contents,
    operand_2=RB.contents,
    su=SU,
    out=EO
)
FR = FlagsRegister("FR", ALU.carry, ALU.zero, clk, load=FI, clr=clr)
RAM = RAM("RAM", databus, MAR.address, load=RI, out=RO)
PC = ProgramCounter("PC", databus, CE, clk, CI, i_clr, CO)
ID = InstructionDecoder("ID", "LUTs/microcode.bin", control_word, IR.opcode, FR.CF, FR.ZF, i_clk, i_clr)

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

@simulation_clock.every(simulation_clock.neg_edge)
@simulation_clock.every(simulation_clock.pos_edge)
def update():
    clk.toggle()
    i_clk.notify()
    # print(databus.state)
    print([sig for sig in control_word])
    #print(bool(ID.microinstruction_counter.clr))
    #print([bool(sig.state) for sig in ID.microinstruction_counter.q])

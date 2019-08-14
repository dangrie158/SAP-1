from simulation import Clock, Signal, State, Junction, Bus
from modules import *

simulation_clock = Clock(freq=1)

databus = Bus("Databus", width=8)

clk = Signal("clk", State.LOW)
i_clk = Signal("!clk", lambda: not clk)
clr = Signal("clr", State.LOW)
i_clr = Signal("clr", lambda: not clk)

AI = Signal("A In", State.HIGH)
AO = Signal("A Out", State.HIGH)

BI = Signal("B In", State.HIGH)

II = Signal("IR In", State.HIGH)
IO = Signal("IR Out", State.HIGH)

MI = Signal("MAR In", State.HIGH)

SU = Signal("ALU Substract", State.LOW)
EO = Signal("ALU Out", State.HIGH)

FI = Signal("Flags In", State.HIGH)

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

EO.state=State.LOW
# print(bool(ALU.zero))


@simulation_clock.every(simulation_clock.neg_edge)
@simulation_clock.every(simulation_clock.pos_edge)
def update():
    clk.toggle()
    print(databus.state)


simulation_clock.run()

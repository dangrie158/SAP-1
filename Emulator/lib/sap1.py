import sys
import os

from .simulation import Signal, State, Junction, Bus
from .modules import *


# add the Spec directory to PYTHONPATH for importing the ISA
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from Spec import ISA
import Tools.asm


class SAP1:

    def __init__(self, simulation_clock):
        self.databus = Bus("Databus", width=8)
        self.control_word = Bus(("Control Word", tuple(ISA.CW.__members__.keys())), width=16)

        self.clk = Signal("CLK", State.LOW)
        self.i_clk = Signal("!CLK", lambda: not self.clk)
        self.clr = Signal("CLR", State.LOW)
        self.i_clr = Signal("!CLR", lambda: not self.clr)

        self.RA = DataRegister("RA", self.databus, self.clk, load=self.control_word['AI'], out=self.control_word['AO'], clr=self.clr)
        self.RB = DataRegister("RB", self.databus, self.clk, load=self.control_word['BI'], out=Signal.VCC, clr=self.clr)
        self.IR = InstructionRegister("IR", self.databus, self.clk, load=self.control_word['II'], out=self.control_word['IO'], clr=self.clr)
        self.MAR = MemoryAddressRegister("MAR", self.databus, self.clk, load=self.control_word['MI'], clr=self.clr)
        self.ALU = ALU(
            "ALU",
            self.databus,
            operand_1=self.RA.contents,
            operand_2=self.RB.contents,
            su=self.control_word['SU'],
            out=self.control_word['EO']
        )
        self.FR = FlagsRegister("FR", self.ALU.carry, self.ALU.zero, self.clk, load=self.control_word['FI'], clr=self.clr)
        self.RAM = RAM("RAM", self.databus, self.MAR.address, self.clk, load=self.control_word['RI'], out=self.control_word['RO'])
        self.PC = ProgramCounter("PC", self.databus, self.control_word['CE'], self.clk, self.control_word['JP'], self.i_clr, self.control_word['CO'])
        self.ID = InstructionDecoder("ID", "LUTs/microcode.bin", self.control_word, self.IR.opcode, self.FR.CF, self.FR.ZF, self.i_clk, self.i_clr)
        self.OUT = OutputDisplay("OUT", self.databus, self.clk, self.control_word['OI'], self.i_clr)

        # register for state updates on simulation clock cycles
        simulation_clock.every(simulation_clock.neg_edge)(lambda: self.update())
        simulation_clock.every(simulation_clock.pos_edge)(lambda: self.update())


    def load_program(self, program_file):
        if program_file.lower().endswith('.s'):
            # assemble the file on-the-fly
            assembly = Tools.asm.parseFile(program_file).assemble()
            contents = b''
            for address in range(0xF + 1):
                data = assembly[address] if address in assembly else b"\0"
                contents += data

        elif program_file.lower().endswith('.bin'):
            with open(program_file, 'rb') as file:
                contents = file.read()
                print(contents)
        else:
            raise TypeError("Can only run assembly code [*.s|*.S] or assembled files [*.bin]")

        self.RAM.load_contents(contents)

    # print(bool(ALU.zero))
    # BI.state = State.LOW
    # AI.state = State.LOW
    # val1 = State.HIGH
    # val2 = State.LOW
    # test = [Signal(initial= lambda: val1) for _ in range(4)] + [Signal(initial= lambda: val2) for _ in range(4)]

    # self.databus.append(test)
    # self.clk.toggle()
    # self.clk.toggle()
    # BI.state = State.HIGH
    # AI.state = State.HIGH
    # val1 = State.HIGH_Z
    # val2 = State.HIGH_Z

    # EO.state=State.LOW
    # print(bool(ALU.zero))

    # CO.state = State.LOW
    # CE.state = State.HIGH

    def update(self):
        self.clk.toggle()
        self.clk.notify()
        self.i_clk.notify()

        print("-"*20)
        opcode_num = Bus.to_int(self.IR.opcode)
        print(f"Instruction {ISA.InstructionSet.by_opcode(opcode_num).name}")
        print(f"program counter {self.PC.counter.count}")
        print(f"memory address {Bus.to_int(self.MAR.address)}")
        print(f"RA contents {Bus.to_int(self.RA.contents)}")
        print(f"RB contents {Bus.to_int(self.RB.contents)}")
        print(f"IR contents {Bus.to_int(self.IR.contents)}")
        print(f"Output contents {Bus.to_int(self.OUT.contents)}")



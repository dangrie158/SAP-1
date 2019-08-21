import sys
import os
from enum import IntEnum
from collections import deque
from pathlib import Path
import time

from .simulation import Signal, State, Junction, Bus
from .modules import *


# add the main directory to PYTHONPATH for importing the ISA
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import Tools.asm
from Spec import ISA


class SAP1:

    class ClockSource(IntEnum):
        RUNNING = 0
        SINGLE_STEP = 1
        HALTED = 2

    def __init__(self, simulation_clock):
        self.databus = Bus("Databus", width=8)
        self.control_word = Bus(("Control Word", tuple(ISA.CW.__members__.keys())), width=16)

        self.clock_source = self.ClockSource.RUNNING
        self.past_runtimes = deque(maxlen=5)
        self.last_run_start = time.time()
        self.avg_freq = -1.0
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
        simulation_clock.every(simulation_clock.neg_edge)(lambda: self.step())
        simulation_clock.every(simulation_clock.pos_edge)(lambda: self.step())

        self.program = None

    @property 
    def instruction(self):
        pc_state = Bus.to_int(self.PC.value)
        mi_bus_state = [bool(st) for st in self.ID.microinstruction]
        mi_step = mi_bus_state.index(False) if False in mi_bus_state else 6
        mi_steps_in_fc = len(ISA.InstructionSet.FETCH_CYCLE)
        # offset after the pc has jumped to the next instruction
        # as a last step of eversy fetch cycle
        if (mi_step == mi_steps_in_fc - 1 and bool(self.clk)) or mi_step >= mi_steps_in_fc:
            pc_state -= 1
        
        return pc_state

    def load_program(self, program_file: Path):
        if program_file.name.lower().endswith('.s'):
            # assemble the file on-the-fly
            self.program = Tools.asm.parseFile(program_file)
            assembly = self.program.assemble()
            contents = b''
            for address in range(0xF + 1):
                data = assembly[address] if address in assembly else b"\0"
                contents += data

        elif program_file.name.lower().endswith('.bin'):
            self.program = None
            with open(program_file, 'rb') as file:
                contents = file.read()
        else:
            raise TypeError("Can only run assembly code [*.s|*.S] or assembled files [*.bin]")

        self.RAM.contents = contents

    def step(self, force=False):
        if self.clock_source is self.ClockSource.RUNNING or force:

            # update stats on the falling edge
            if not self.clk:
                self.past_runtimes.append(time.time() - self.last_run_start)
                self.last_run_start = time.time()
                self.avg_freq = len(self.past_runtimes) / sum(self.past_runtimes)
            
            self.clk.toggle()
            self.clk.notify()
            self.i_clk.notify()

        if self.control_word['HLT']:
            self.clock_source = self.ClockSource.HALTED

    def reset(self):
        self.clr.state = State.HIGH
        self.clr.notify()
        self.i_clr.notify()
        self.clr.state = State.LOW
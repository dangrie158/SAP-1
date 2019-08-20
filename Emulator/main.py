from lib.sap1 import SAP1
from lib import display
from lib.simulation import Clock, Bus

import curses
import sys
from pathlib import Path

simulation_clock = Clock(freq=1000)

processor = SAP1(simulation_clock)

program_file = Path("Example-Programs/Counter.bin")
processor.load_program(program_file)


@curses.wrapper
def main(stdscr):
    display.init()
    stdscr.clear()

    cols_x = [3, 25, 45, 67, 88]
    rows_y = [3, 12, 21, 30, 39, 48]
    clk = display.Clock(
        rows_y[0],
        cols_x[0],
        "Processor Clock",
        processor.clk,
        lambda: processor.clock_source,
        lambda: processor.avg_freq,
        width=cols_x[1] - cols_x[0] - 1,
    )
    mar = display.Register(
        rows_y[1],
        cols_x[0],
        "Memory Address",
        processor.MAR.address,
        [processor.control_word["MI"]],
        display.Color.BLUE,
        width=cols_x[1] - cols_x[0] - 1,
    )
    ram = display.Register(
        rows_y[2],
        cols_x[0],
        "RAM",
        processor.RAM.data,
        [processor.control_word["RO"], processor.control_word["RI"]],
        display.Color.RED,
        width=cols_x[1] - cols_x[0] - 1,
    )
    ir = display.InstructionRegister(
        rows_y[3],
        cols_x[0],
        "Instruction Register",
        processor.IR.opcode,
        processor.IR.parameter,
        [processor.control_word["IO"], processor.control_word["II"]],
        width=cols_x[1] - cols_x[0] - 1,
    )
    flags = display.Register(
        rows_y[4],
        cols_x[0],
        "Flags Register",
        [processor.FR.CF, processor.FR.ZF],
        [processor.control_word["FI"]],
        display.Color.BLUE,
        width=cols_x[1] - cols_x[0] - 1,
    )
    pc = display.Register(
        rows_y[0],
        cols_x[2],
        "Program Counter",
        processor.PC.value,
        [
            processor.control_word["CO"],
            processor.control_word["JP"],
            processor.control_word["CE"],
        ],
        display.Color.BLUE,
        width=cols_x[1] - cols_x[0] - 1,
    )
    ra = display.Register(
        rows_y[1],
        cols_x[2],
        "Data Register A",
        processor.RA.contents,
        [processor.control_word["AO"], processor.control_word["AI"]],
        display.Color.RED,
        width=cols_x[1] - cols_x[0] - 1,
    )
    alu = display.Register(
        rows_y[2],
        cols_x[2],
        "Sum Register",
        processor.ALU.contents,
        [
            processor.ALU.zero,
            processor.ALU.carry,
            processor.control_word["EO"],
            processor.control_word["SU"],
        ],
        display.Color.RED,
        width=cols_x[1] - cols_x[0] - 1,
    )
    rb = display.Register(
        rows_y[3],
        cols_x[2],
        "Data Register B",
        processor.RB.contents,
        [processor.control_word["BI"]],
        display.Color.RED,
        width=cols_x[1] - cols_x[0] - 1,
    )
    out = display.OutputDisplay(
        rows_y[4],
        cols_x[2],
        "Output",
        processor.OUT.contents,
        [processor.control_word["OI"]],
        display.Color.RED,
        width=cols_x[1] - cols_x[0] - 1,
    )
    id = display.InstructionDecoder(
        rows_y[5],
        cols_x[0],
        "Instruction Decoder",
        processor.ID.control_word_positive_logic,
        processor.ID.microinstruction,
        display.Color.RED,
        width=max(cols_x) - min(cols_x) - 1,
    )
    db = display.DataBus(
        rows_y[0],
        cols_x[1],
        "Databus",
        processor.databus,
        width=cols_x[2] - cols_x[1] - 1,
        height=max(rows_y) - min(rows_y),
    )

    info = display.EmulatorInfo(
        rows_y[0],
        cols_x[3],
        title="Emulator Info", 
        past_runtimes=lambda: simulation_clock.past_runtimes,
        missed_ticks=lambda: simulation_clock.missed_ticks,
        width=cols_x[3] - cols_x[2] - 1,
    )

    keys = display.ControlsInfo(
        rows_y[1],
        cols_x[3],
        title="Controls", 
        keybindings={
            'c': 'Toggle Clock',
            'o': 'Open Assembly',
            'n': 'Single Step',
            'r': 'Reset Processor',
            'q': 'Quit'
        },
        width=cols_x[3] - cols_x[2] - 1,
    )

    disassembler = display.Disassembly(
        rows_y[2],
        cols_x[3],
        title=program_file.name,
        current_instruction=lambda: processor.instruction,
        width=cols_x[3] - cols_x[2] - 1,
    )

    disassembler.assembly = (
        processor.program if processor.program is not None else processor.RAM.contents
    )

    @simulation_clock.every(simulation_clock.neg_edge)
    @simulation_clock.every(simulation_clock.pos_edge)
    def render():
        clk.render()
        mar.render()
        ram.render()
        ir.render()
        flags.render()

        pc.render()
        ra.render()
        alu.render()
        rb.render()
        out.render()

        id.render()

        db.render()

        info.render()
        keys.render()
        disassembler.render()

        curses.doupdate()

    # start the emulation clock
    try:
        simulation_clock.start()
    except KeyboardInterrupt:
        sys.exit(0)


main()

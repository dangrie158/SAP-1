from lib.sap1 import SAP1
from lib import display
from lib.simulation import Clock, Bus

import curses
import sys

simulation_clock = Clock(freq=5)

processor = SAP1(simulation_clock)

processor.load_program("Example-Programs/Counter.s")


@curses.wrapper
def main(stdscr):
    display.init()
    stdscr.clear()

    cols_x = [3, 25, 46, 69]
    rows_y = [3, 12, 21, 30, 39, 48]
    clk = display.Clock(
        rows_y[0],
        cols_x[0],
        "Processor Clock",
        processor.clk,
        lambda: processor.clock_source,
        lambda: processor.avg_freq,
        width=cols_x[1]-cols_x[0] - 1
    )
    mar = display.Register(
        rows_y[1],
        cols_x[0],
        "Memory Address",
        processor.MAR.address,
        [processor.control_word["MI"]],
        display.Color.BLUE,
        width=cols_x[1]-cols_x[0] - 1
    )
    ram = display.Register(
        rows_y[2],
        cols_x[0],
        "RAM",
        processor.RAM.data,
        [processor.control_word["RO"], processor.control_word["RI"]],
        display.Color.RED,
        width=cols_x[1]-cols_x[0] - 1
    )
    ir = display.InstructionRegister(
        rows_y[3],
        cols_x[0],
        "Instruction Register",
        processor.IR.opcode,
        processor.IR.parameter,
        [processor.control_word["IO"], processor.control_word["II"]],
        width=cols_x[1]-cols_x[0] - 1
    )
    flags = display.Register(
        rows_y[4],
        cols_x[0],
        "Flags Register",
        [processor.FR.CF, processor.FR.ZF],
        [processor.control_word["FI"]],
        display.Color.BLUE,
        width=cols_x[1]-cols_x[0] - 1
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
        width=cols_x[1]-cols_x[0] - 1
    )
    ra = display.Register(
        rows_y[1],
        cols_x[2],
        "Data Register A",
        processor.RA.contents,
        [processor.control_word["AO"], processor.control_word["AI"]],
        display.Color.RED,
        width=cols_x[1]-cols_x[0] - 1
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
        width=cols_x[1]-cols_x[0] - 1
    )
    rb = display.Register(
        rows_y[3],
        cols_x[2],
        "Data Register B",
        processor.RB.contents,
        [processor.control_word["BI"]],
        display.Color.RED,
        width=cols_x[1]-cols_x[0] - 1
    )
    out = display.OutputDisplay(
        rows_y[4],
        cols_x[2],
        "Output",
        processor.OUT.contents,
        [processor.control_word["OI"]],
        display.Color.RED,
        width=cols_x[1]-cols_x[0] - 1
    )
    id = display.InstructionDecoder(
        rows_y[5],
        cols_x[0],
        "Instruction Decoder",
        processor.ID.control_word_positive_logic,
        processor.ID.microinstruction,
        display.Color.RED,
        width=max(cols_x)-min(cols_x) - 2
    )
    db = display.DataBus(
        rows_y[0],
        cols_x[1],
        "Databus",
        processor.databus,
        width=cols_x[2] - cols_x[1] - 1,
        height=max(rows_y) - min(rows_y)
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
        curses.doupdate()

    # start the emulation clock
    try:
        simulation_clock.start()
    except KeyboardInterrupt:
        sys.exit(0)


main()

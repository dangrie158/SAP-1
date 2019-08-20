import functools
import math
import os
import sys
from typing import Sequence
from os import linesep
from enum import IntEnum
from .simulation import Signal, Bus, State
from .sap1 import SAP1
from textwrap import dedent

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from Spec import ISA

import curses


def multisegment_number(number, num_digits, width):
    output = []
    output_line = ""
    spacer = " "

    for line in range(3):
        for num in f"{{:0{num_digits}d}}".format(number):
            output_line += segment(num).split("\n")[line] + spacer
        output.append(output_line.center(width))
        output_line = ""
    return "".join(output)


def segment(number):
    return {
        "0": """
┌─┐
│ │
└─┘""",
        "1": """
  ╷
  │
  ╵""",
        "2": """
╶─┐
┌─┘
└─╴""",
        "3": """
╶─┐
╶─┤
╶─┘""",
        "4": """
╷ ╷
└─┤
  ╵""",
        "5": """
┌─╴
└─┐
╶─┘""",
        "6": """
┌─╴
├─┐
└─┘""",
        "7": """
╶─┐
  │
  ╵""",
        "8": """
┌─┐
├─┤
└─┘""",
        "9": """
┌─┐
└─┤
╶─┘""",
    }[number][1:]


class Color(IntEnum):
    WHITE = 1
    RED = 2
    BLUE = 3
    GREEN = 4


def init():
    curses.use_default_colors()
    curses.init_pair(Color.WHITE, curses.COLOR_WHITE, -1)
    curses.init_pair(Color.RED, curses.COLOR_RED, -1)
    curses.init_pair(Color.BLUE, curses.COLOR_BLUE, -1)
    curses.init_pair(Color.GREEN, curses.COLOR_GREEN, -1)
    curses.curs_set(0)


def led_array(num, width, spacer=" "):
    return (
        format(num, f"0{width}b").replace("0", f"○{spacer}").replace("1", f"●{spacer}")
    )


class Register:
    def __init__(
        self,
        y: int,
        x: int,
        name: str,
        signals: Sequence[Signal],
        control_lines: Sequence[Signal],
        color: Color,
        width: int,
    ):
        self.name = name
        self.signals = signals
        self.control_lines = control_lines

        self.color = color

        self.width = width
        self.height = 7 + math.ceil(len(control_lines) / 2)

        self.win = curses.newwin(self.height, self.width, y, x)

    def render(self):
        reg_value = Bus.to_int(self.signals)
        self.win.addstr(1, 0, self.name.center(self.width))
        self.win.hline(2, 0, curses.ACS_HLINE, self.width)
        self.win.addstr(
            3,
            0,
            led_array(reg_value, len(self.signals)).center(self.width),
            curses.color_pair(self.color),
        )
        self.win.addstr(4, 0, ("0x" + format(reg_value, "02X")).center(self.width))
        if len(self.control_lines) > 0:
            self.win.hline(5, 0, curses.ACS_HLINE, self.width)
            self.state_box(6, 1)
        self.win.border()

        self.win.noutrefresh()

    def state_box(self, y: int, x: int):
        """
        rendering the signal in a box with a color depending on their state
        """
        width = self.width

        for i, signal in enumerate(self.control_lines):
            display_color = {
                State.HIGH: Color.GREEN,
                State.LOW: Color.RED,
                State.HIGH_Z: Color.WHITE,
            }[signal.state]

            # use the last part of the fully qualiifed name
            display_name = signal.name.split(":")[-1].center(width // 2)
            self.win.addstr(
                y + (i // 2),
                x + ((width // 2) * (i % 2)),
                display_name,
                curses.color_pair(display_color.value),
            )

        self.win.vline(
            y, width // 2, curses.ACS_VLINE, math.ceil(len(self.control_lines) / 2)
        )


class InstructionRegister(Register):
    def __init__(
        self,
        y: int,
        x: int,
        name: str,
        opcode: Sequence[Signal],
        parameter: Sequence[Signal],
        control_lines: Sequence[Signal],
        width: int,
    ):
        super().__init__(y, x, name, [], control_lines, Color.RED, width)
        self.opcode = opcode
        self.parameter = parameter
        self.height = 8 + math.ceil(len(control_lines) / 2)
        self.win.resize(self.height, self.width)

    def render(self):
        # title
        self.win.addstr(1, 0, self.name.center(self.width))
        self.win.hline(2, 0, curses.ACS_HLINE, self.width)

        # opcode
        opcode_val = Bus.to_int(self.opcode)
        self.win.addstr(
            3,
            1,
            led_array(opcode_val, len(self.opcode)).center(self.width // 2),
            curses.color_pair(Color.BLUE),
        )
        self.win.addstr(
            4, 1, ("0x" + format(opcode_val, "02X")).center(self.width // 2)
        )

        # parameter
        param_val = Bus.to_int(self.parameter)
        self.win.addstr(
            3,
            self.width // 2 + 1,
            led_array(param_val, len(self.parameter)).center(self.width // 2),
            curses.color_pair(Color.RED),
        )
        self.win.addstr(
            4,
            self.width // 2 + 1,
            ("0x" + format(param_val, "02X")).center(self.width // 2),
        )
        # opcode name and param
        isa_instruction =  ISA.InstructionSet.by_opcode(opcode_val)
        self.win.addstr(
            5,
            6,
            isa_instruction.name,
            curses.color_pair(Color.BLUE)
        )
        if isa_instruction.has_parameter:
            self.win.addstr(
                5,
                7 + len(isa_instruction.name),
                f"(0x{param_val:02X})",
                curses.color_pair(Color.RED)
            )

        # control lines
        self.win.hline(6, 0, curses.ACS_HLINE, self.width)
        self.state_box(7, 1)
        self.win.border()

        self.win.noutrefresh()

class OutputDisplay(Register):
    def __init__(
        self,
        y: int,
        x: int,
        name: str,
        signals: Sequence[Signal],
        control_lines: Sequence[Signal],
        color: Color,
        width: int,
    ):
        super().__init__(y, x, name, signals, control_lines, color, width)
        self.height = 8 + math.ceil(len(control_lines) / 2)
        self.win.resize(self.height, self.width)

    def render(self):
        reg_value = Bus.to_int(self.signals)
        self.win.addstr(1, 0, self.name.center(self.width))
        self.win.hline(2, 0, curses.ACS_HLINE, self.width)
        self.win.addstr(
            3,
            0,
            multisegment_number(reg_value, 4, self.width).center(self.width),
            curses.color_pair(self.color),
        )
        if len(self.control_lines) > 0:
            self.win.hline(6, 0, curses.ACS_HLINE, self.width)
            self.state_box(7, 1)
        self.win.border()

        self.win.noutrefresh()


class InstructionDecoder:
    def __init__(
        self,
        y: int,
        x: int,
        name: str,
        signals: Sequence[Signal],
        mi_counter: Sequence[Signal],
        color: Color,
        width: int,
    ):
        self.name = name
        self.signals = signals
        self.mi_counter = mi_counter

        self.color = color

        self.width = width
        self.height = 8

        self.win = curses.newwin(self.height, self.width, y, x)

    def render(self):
        # title
        self.win.addstr(1, 0, self.name.center(self.width))
        self.win.hline(2, 0, curses.ACS_HLINE, self.width)

        # micro instruction counter
        cw_width = 36
        counter_width = self.width - cw_width - 3
        count_value = Bus.to_int(self.mi_counter, order="big")
        bus_state = [bool(st) for st in self.mi_counter]
        step = bus_state.index(False) if False in bus_state else 6
        self.win.addstr(3, 1, "Microinstuction".center(counter_width - 1))
        self.win.addstr(4, 1, f"0x{step:02X}".center(counter_width - 1))
        self.win.addstr(
            5,
            2,
            led_array(count_value, 5, spacer="   ").center(counter_width),
            curses.color_pair(Color.GREEN),
        )
        self.signal_names(6, 2 + (counter_width // 2) - ((5 * 4) // 2), self.mi_counter)

        # control word
        cw_start = self.width - cw_width
        self.win.vline(3, cw_start, curses.ACS_VLINE, self.height - 3)
        reg_value_lower = Bus.to_int(self.signals[:8])
        reg_value_upper = Bus.to_int(self.signals[8:])
        self.signal_names(3, cw_start + 3, self.signals[:8])
        self.win.addstr(
            4,
            cw_start + 4,
            led_array(reg_value_lower, 8, spacer="   "),
            curses.color_pair(self.color),
        )
        self.win.addstr(
            5,
            cw_start + 4,
            led_array(reg_value_upper, 8, spacer="   "),
            curses.color_pair(self.color),
        )
        self.signal_names(6, cw_start + 3, self.signals[8:])

        self.win.border()

        self.win.noutrefresh()

    def signal_names(self, y: int, x: int, signals):
        """
        rendering the signal in a box with a color depending on their state
        """
        width = self.width

        for i, signal in enumerate(signals):
            display_color = {
                State.HIGH: Color.GREEN,
                State.LOW: Color.RED,
                State.HIGH_Z: Color.WHITE,
            }[signal.state]

            display_name = signal.name.split(":")[-1]
            self.win.addstr(
                y, x + 4 * i, display_name, curses.color_pair(display_color.value)
            )


class Clock:
    def __init__(
        self,
        y: int,
        x: int,
        name: str,
        clock: Signal,
        source: SAP1.ClockSource,
        avg_freq: float,
        width: int,
    ):
        self.name = name
        self.clock = clock
        self.source = source
        self.freq = avg_freq

        self.width = width
        self.height = 8

        self.win = curses.newwin(self.height, self.width, y, x)

    def render(self):
        clock_state = bool(self.clock)
        self.win.addstr(1, 0, self.name.center(self.width))
        self.win.hline(2, 0, curses.ACS_HLINE, self.width)

        self.win.addstr(3, 3, "State:")
        self.win.addstr(
            3,
            11,
            f'{"HIGH" if clock_state else "LOW "} {led_array(int(clock_state), 1, spacer="")}',
            curses.color_pair(Color.GREEN if clock_state else Color.RED),
        )

        self.win.addstr(4, 3, "Source:")
        source_color, source_text = {
            SAP1.ClockSource.RUNNING: (Color.GREEN, "RUN "),
            SAP1.ClockSource.SINGLE_STEP: (Color.BLUE, "STEP"),
            SAP1.ClockSource.HALTED: (Color.RED, "HALT"),
        }[self.source()]
        self.win.addstr(4, 11, source_text, curses.color_pair(source_color))

        self.win.addstr(5, 3, f"Freq: {self.freq():06.2f} Hz")

        self.win.border()

        self.win.noutrefresh()


class DataBus:
    def __init__(
        self,
        y: int,
        x: int,
        name: str,
        signals: Sequence[Signal],
        height: int,
        width: int,
    ):
        self.name = name
        self.signals = signals

        self.y = y
        self.x = x
        self.height = height
        self.width = width

        self.win = curses.newwin(self.height, self.width, y, x)

    def render(self):
        self.win.addstr(1, 0, self.name.center(self.width))
        self.win.hline(2, 0, curses.ACS_HLINE, self.width)
        self.win.addstr(3, 3, " ".join(str(i) for i in range(len(self.signals), 0, -1)))
        for i, signal in enumerate(self.signals):
            color = {
                State.HIGH: Color.GREEN,
                State.LOW: Color.RED,
                State.HIGH_Z: Color.BLUE,
            }[signal.state]
            self.colored_vline(5, 3 + 2 * i, self.height - 2, color)

        self.win.border()

        self.win.noutrefresh()

    def colored_vline(self, y, x, height, color):
        for i in range(height - y):
            self.win.addch(y + i, x, curses.ACS_VLINE, curses.color_pair(color))

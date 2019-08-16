import math
import random
from typing import Sequence, Mapping, Optional
from types import MethodType
from pprint import pformat
from functools import partial

from simulation import Signal, State, Bus


class IC:
    input_signals = []
    output_signals = {}
    input_busses = {}
    output_busses = {}

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):

        self.name = name
        if self.name is None:
            self.name = self.__class__.__name__

        for signal_name in self.input_signals:
            setattr(
                self,
                signal_name,
                kwargs.pop(
                    signal_name,
                    Signal(f"{self.name}:{signal_name.upper()}", State.HIGH),
                ),
            )

        for bus_name, width in self.input_busses.items():
            setattr(
                self,
                bus_name,
                kwargs.pop(
                    bus_name,
                    [
                        Signal(f"{self.name}:{bus_name.upper()}{sig_num}", State.HIGH)
                        for sig_num in range(width)
                    ],
                ),
            )
            # check if the created bus has actually the required length
            IC.check_bus_length(getattr(self, bus_name), width)

        # create the output signal getters
        for signal_name, state_fun in self.output_signals.items():
            setattr(
                self,
                signal_name,
                Signal(
                    f"{self.name.upper()}:{signal_name.upper()}",
                    MethodType(state_fun, self),
                ),
            )

        # create the output bus getters
        for bus_name, bus_info in self.output_busses.items():
            bus_width, bit_fun = bus_info
            setattr(
                self,
                bus_name,
                [
                    Signal(
                        f"{self.name.upper()}:{bus_name.upper()}{bit}",
                        partial(MethodType(bit_fun, self), bit),
                    )
                    for bit in range(bus_width)
                ],
            )

        unknown_signals = [
            signal for signal in kwargs.keys() if signal not in self.signals
        ]
        if len(unknown_signals) > 0:
            raise ValueError(f"provided unknown signal names: {unknown_signals}")

    def get_bus_output(self, bus_name, bus_width, bit_fun):
        return

    def get_signal_output(self, signal_name, state_fun):
        return Signal(f"{self.name}:{signal_name}", bit_fun)

    def __str__(self):
        return f"IC<{self.name}>: { pformat({signal: pformat(getattr(self, signal)) for signal in self.signals }) }"

    @classmethod
    def check_bus_length(cls, bus, target_width):
        if not hasattr(bus, "__len__") or len(bus) != target_width:
            raise ValueError(
                f"{cls.__name__} takes exacly {target_width} input signals in '{bus[0].get('name', '<unknown bus>')}'"
            )


class SN74LS00(IC):
    """
    Quad 2-input positive-NAND gates
    """

    num_gates = 4
    input_busses = {"a": num_gates, "b": num_gates}

    output_busses = {
        "z": (num_gates, lambda self, bit: not (self.a[bit] and self.b[bit]))
    }


class SN74LS02(IC):
    """
    Quadruple 2-input positive-NOR gates
    """

    num_gates = 4
    input_busses = {"a": num_gates, "b": num_gates}

    output_busses = {
        "z": (num_gates, lambda self, bit: not (self.a[bit] or self.b[bit]))
    }


class SN74LS04(IC):
    """
    Hex Inverter
    """

    num_gates = 6
    input_busses = {"a": num_gates}

    output_busses = {"z": (num_gates, lambda self, bit: not self.a[bit])}


class SN74LS08(IC):
    """
    Quadruple 2-input positive-AND gates
    """

    num_gates = 4
    input_busses = {"a": num_gates, "b": num_gates}

    output_busses = {"z": (num_gates, lambda self, bit: self.a[bit] and self.b[bit])}


class SN74LS86(IC):
    """
    Quadruple 2-Input Exclusive-OR Gate
    """

    num_gates = 4
    input_busses = {"a": num_gates, "b": num_gates}

    output_busses = {
        "z": (num_gates, lambda self, bit: bool(self.a[bit]) != bool(self.b[bit]))
    }


class SN74LS138(IC):
    """
    1−of−8 Decoder/ Demultiplexer
    """

    num_bits = 8
    num_addr_lines = math.ceil(math.log2(num_bits))

    input_signals = ["g1", "g2a", "g2b"]
    input_busses = {"a": num_addr_lines}
    output_busses = {
        "y": (
            num_bits,
            lambda self, bit: (State.from_bool(Bus.to_int(self.a) == bit))
            if self.g1 and (not self.g2a and not self.g2b)
            else State.HIGH_Z,
        )
    }


class SN74LS161(IC):
    """
    Synchronous 4-bit counter
    """

    num_bits = 4
    input_signals = ["clk", "enp", "ent", "ld", "clr"]
    input_busses = {"a": num_bits}
    output_busses = {
        "q": (
            num_bits,
            lambda self, x: State.from_bool(format(self.count, "04b")[x] == "1"),
        )
    }

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)
        self.count = 0

        self.clk.on_change(self._load)
        self.clr.on_change(self._clear)

    def _load(self, new_val):
        if self.clk and not self.ld:
            self.count = Bus.to_int(self.a)

        if self.clk and self.enp and self.ent:
            self.count += 1
            self.count %= 2 ** self.num_bits

    def _clear(self, new_val):
        # clear on rising edge of clear
        if not self._clear:
            self.count = 0


class SN74LS173(IC):
    """
    4-Bit D-Type Registers With 3-State Outputs
    """

    num_bits = 4
    input_signals = ["clk", "m", "n", "g1", "g2", "clr"]
    input_busses = {"d": num_bits}

    output_busses = {
        "q": (
            num_bits,
            lambda self, bit: self.reg[bit]
            if not self.m and not self.n
            else State.HIGH_Z,
        )
    }

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)

        # initially the register contents are 0
        self.reg = [State.LOW] * 4

        self.clk.on_change(self._update)
        self.g1.on_change(self._update)
        self.g2.on_change(self._update)
        self.clr.on_change(self.clear)

    def _update(self, _) -> None:
        if not self.clr:
            if self.clk:
                # rising edge of the clock

                if not self.g1 and not self.g2:
                    # latch the data in
                    for num in range(self.num_bits):
                        self.reg[num] = self.d[num].state

    def clear(self) -> None:
        # the clear bit is active-high
        if self.clear:
            for bit in range(self.num_bits):
                self.reg[bit] = State.LOW


class SN74LS189(IC):
    """
    64-Bit Random Access Memory with 3-STATE Outputs
    """

    num_bits = 64
    word_width = 4
    num_words = num_bits // word_width
    num_addr_bits = math.ceil(math.log2(num_words))

    def get_output_bit(self, bit) -> Signal:
        if not self.cs and self.we:
            address = Bus.to_int(self.a)
            contents = self.contents[address]
            return State.HIGH if format(contents[bit], "04b")[bit] == "1" else State.LOW
        else:
            return State.HIGH_Z

    input_signals = ["cs", "we"]
    input_busses = {"a": num_addr_bits, "d": num_addr_bits}
    output_busses = {"o": (word_width, get_output_bit)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the ram content buffer (initialize randomly)
        # just like the real thing would do
        self.contents = [random.getrandbits(SN74LS189.word_width)] * self.num_words

        # write the data contents on the falling edge of the erite pin
        self.we.on_change(lambda x: self._write_word() if not x else None)

    def _write_word():
        if not self.cs:
            input_val = Bus.to_int(self.d)
            address = Bus.to_int(self.a)

            self.contents[address] = input_val


class SN74LS245(IC):
    """
    Octal Bus Transceiver
    """

    num_bits = 8
    input_signals = ["dir", "g"]
    input_busses = {"a": num_bits}
    output_busses = {
        "b": (num_bits, lambda self, x: self.a[x] if not self.g else State.HIGH_Z)
    }

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)

        self.dir.on_change(
            lambda x: ValueError(
                "Bidirectional Operation not supported. 'dir' pin needs to be tied high"
            )
            if not x
            else None
        )


class SN74LS283(IC):
    """
    4-Bit Binary Full Adders With Fast Carry
    """

    num_bits = 4
    input_signals = ["c0"]
    input_busses = {"a": num_bits, "b": num_bits}
    output_signals = {"c4": lambda self: self._get_carry_bit(3)}
    output_busses = {"e": (num_bits, lambda self, bit: partial(self._get_bit, bit))}

    def _partial_sum(self, x):
        return sum(
            [1 for bit in [self.a[x], self.b[x], self._get_carry_bit(x - 1)] if bit]
        )

    def _get_carry_bit(self, x):
        return self.c0 if x == -1 else self._partial_sum(x) > 1

    def _get_bit(self, x):
        return State.HIGH if self._partial_sum(x) in (1, 3) else State.LOW

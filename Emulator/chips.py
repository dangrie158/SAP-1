from simulation import Signal, State, Bus
from typing import Sequence, Mapping, Optional
from pprint import pformat
from functools import partial


class IC:
    signals = []

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):

        self.name = name
        if self.name is None:
            self.name = self.__class__.__name__

        for signal_name in self.signals:
            setattr(
                self,
                signal_name,
                kwargs.pop(
                    signal_name,
                    Signal(f"{self.name}:{signal_name.upper()}", State.HIGH),
                ),
            )

        unknown_signals = [
            signal for signal in kwargs.keys() if signal not in self.signals
        ]
        if len(unknown_signals) > 0:
            raise ValueError(f"provided unknown signal names: {unknown_signals}")

    def __str__(self):
        return f"IC<{self.name}>: { pformat({signal: pformat(getattr(self, signal)) for signal in self.signals }) }"

    def check_bus_length(self, bus, target_width):
        if not hasattr(bus, "__len__") or len(bus) != target_width:
            raise ValueError(
                f"{self.__class__.__name__} takes exacly {target_width} input signals in '{bus.__dict__.get('name', '<unknown bus>')}'"
            )


class LogicGate(IC):
    """
    A general logic gate with multiple gates. 
    """

    signals = ["a", "b"]

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)

        super().check_bus_length(self.a, self.num_gates)
        super().check_bus_length(self.b, self.num_gates)

    def get_output(self, bit):
        raise NotImplementedError("You need to implement a logic function")

    @property
    def z(self) -> Sequence[Signal]:
        get_bit = lambda bit: self.a[bit] != self.b[bit]

        return [
            Signal(f"{self.name}:Z{bit}", partial(self.get_output, bit))
            for bit in range(self.num_gates)
        ]
        return Bus(
            f"{self.name}:Z",
            [
                Signal(f"{self.name}:Z{bit}", partial(self.get_output, bit))
                for bit in range(self.num_gates)
            ],
        )


class SN74LS02(LogicGate):
    """
    Quadruple 2-input positive-NOR gates
    """

    num_gates = 4

    def get_output(self, bit):
        # NOR
        return not self.a[bit] or self.b[bit]


class SN74LS08(LogicGate):
    """
    Quadruple 2-input positive-AND gates
    """

    num_gates = 4

    def get_output(self, bit):
        # AND
        return self.a[bit] and self.b[bit]


class SN74LS86(LogicGate):
    """
    Quadruple 2-Input Exclusive-OR Gate
    """

    num_gates = 4

    def get_output(self, bit):
        # logical xor
        return bool(self.a[bit]) != bool(self.b[bit])


class SN74LS173(IC):
    """
    4-Bit D-Type Registers With 3-State Outputs
    """

    num_bits = 4
    signals = ["d", "clk", "m", "n", "g1", "g2", "clr"]

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)

        super().check_bus_length(self.d, self.num_bits)

        # initially the register contents are 0
        self.reg = [
            Signal(f"{self.name}:D{num}", State.LOW) for num in range(self.num_bits)
        ]

        self.clk.on_change(self._update)
        self.g1.on_change(self._update)
        self.g2.on_change(self._update)
        self.clr.on_change(self.clear)

    @property
    def q(self) -> Sequence[Signal]:
        get_bit = (
            lambda bit: self.reg[bit] if not self.m and not self.n else State.HIGH_Z
        )

        return [
            Signal(f"{self.name}:D{bit}", partial(get_bit, bit))
            for bit in range(self.num_bits)
        ]

    def _update(self, _) -> None:
        if not self.clr:
            if self.clk:
                # rising edge of the clock

                if not self.g1 and not self.g2:
                    # latch the data in
                    for num in range(self.num_bits):
                        self.reg[num].state = self.d[num].state

    def clear(self) -> None:
        # the clear bit is active-high
        if self.clear:
            for bit in range(self.num_bits):
                self.reg[bit].set(State.LOW)


class SN74LS245(IC):
    """
    Octal Bus Transceiver
    """

    num_bits = 8
    signals = ["a", "dir", "g"]

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)

        super().check_bus_length(self.a, self.num_bits)

        if not self.dir:
            raise ValueError(
                "Bidirectional Operation not supported. 'dir' pin needs to be tied high"
            )

    @property
    def b(self):
        get_bit = lambda x: self.a[x] if not self.g else State.HIGH_Z

        return [
            Signal(f"{self.name}:B{bit}", partial(get_bit, bit))
            for bit in range(self.num_bits)
        ]


class SN74LS283(IC):
    """
    4-Bit Binary Full Adders With Fast Carry
    """

    num_bits = 4
    signals = ["a", "b", "c0"]

    def __init__(self, name: Optional[str] = None, **kwargs: Mapping[str, Signal]):
        super().__init__(name, **kwargs)

        super().check_bus_length(self.a, self.num_bits)
        super().check_bus_length(self.b, self.num_bits)

        self._partial_sum = lambda x: sum(
            [1 for bit in [self.a[x], self.b[x], self._get_carry_bit(x - 1)] if bit]
        )
        self._get_carry_bit = lambda x: self.c0 if x == -1 else self._partial_sum(x) > 1
        self._get_bit = (
            lambda x: State.HIGH if self._partial_sum(x) in (1, 3) else State.LOW
        )

    @property
    def e(self):
        return [
            Signal(f"{self.name}:E{bit}", partial(self._get_bit, bit))
            for bit in range(self.num_bits)
        ]
        return Bus(
            f"{self.name}:E",
            [
                Signal(f"{self.name}:E{bit}", partial(self._get_bit, bit))
                for bit in range(self.num_bits)
            ],
        )

    @property
    def c4(self):
        return Signal(f"{self.name}:C4", lambda: self._get_carry_bit(3))

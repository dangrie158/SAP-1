import threading
import time
from enum import Enum
from pprint import pformat
from typing import Callable, Union, Optional, Sequence
from collections import deque


class State(Enum):
    LOW = 0
    HIGH = 1
    HIGH_Z = 2

    @staticmethod
    def from_bool(state: bool) -> "State":
        return State.HIGH if state else State.LOW

    def __bool__(self) -> bool:
        if self is State.HIGH_Z:
            raise ValueError(f"tried to read HIGH_Z signal")

        if self is State.HIGH:
            return True
        else:
            return False


class Signal:
    sig_num: int = 0

    def __init__(self, name: str = None, initial: State = State.HIGH_Z):
        self.name = name
        self.handlers = []
        self._state = initial
        if not self.name:
            self.name = f"Signal #{Signal.sig_num:04d}"
        Signal.sig_num += 1

    def on_change(self, handler: Callable) -> Callable:
        if handler not in self.handlers:
            self.handlers.append(handler)
        return handler

    @property
    def state(self) -> State:
        if isinstance(self._state, bool):
            return State.from_bool(self._state)

        state = self._state
        while hasattr(state, "__call__"):
            state = Signal(self.name, self._state())
        if isinstance(state, Signal):
            return state.state
        else:
            return state

    @state.setter
    def state(self, new_state: Union[State, bool]) -> None:
        has_changed = self.state != new_state
        self._state = new_state
        if has_changed:
            self.notify()

    def notify(self):
        for handler in self.handlers:
            handler(self._state)

    def toggle(self) -> None:
        self.state = not self.state

    def __bool__(self) -> bool:
        return bool(self.state)

    def __repr__(self) -> str:
        return f"Signal({self.name}: {self.state})"


Signal.GND = Signal("Ground", State.LOW)
Signal.VCC = Signal("VCC", State.HIGH)
Signal.FLOATING = Signal("unconnected", State.HIGH_Z)


class Junction:
    junction_num: int = 0

    def __init__(self, name: str = None, initial: Optional[State] = None):
        self.name = name
        self.handlers = []
        self._signals = []
        if initial is not None:
            self.append(initial)

        if not self.name:
            self.name = f"Junction #{Junction.junction_num:04d}"
            Junction.junction_num += 1

    def append(self, signal: Union[Signal, "Junction"]) -> None:
        if isinstance(signal, Junction):
            self._signals.append(signal._signals)
        else:
            self._signals.append(signal)

    def on_change(self, handler: Callable) -> Callable:
        for signal in self._signals:
            signal.on_change(handler)

        return handler

    @property
    def state(self) -> State:
        driving_signals = [
            signal for signal in self._signals if signal.state is not State.HIGH_Z
        ]

        if len(driving_signals) == 0:
            return State.HIGH_Z
        else:
            if len(driving_signals) > 1:
                raise ValueError(
                    f"More that one driving (non High Z) signal in junction {self.name}: {[sig.name for sig in driving_signals]}"
                )

            return driving_signals[0].state

    def __bool__(self) -> bool:
        return bool(self.state)

    def __repr__(self) -> str:
        return f"Junction({self.name}: {pformat([signal for signal in self._signals])})"


class Bus:
    def __init__(self, name, width):
        if hasattr(name, '__len__') and len(name) == 2:
            self.name, line_names = name
            if len(line_names) != width:
                raise ValueError(f"When passing names for the individual lines, you need to pass exactly the same number of names as the bus '{self.name}' is wide")
        else:
            self.name, line_names = name, [f"D{num}" for num in range(width)]
        self._lines = [Junction(f"{line_names[num]}") for num in range(width)]

    @property
    def state(self) -> Sequence[State]:
        return [line.state for line in self._lines]

    def __repr__(self) -> str:
        return f"Bus({self.name}: {pformat([line for line in self._lines])})"

    def append(self, signals):
        if len(signals) != len(self._lines):
            raise ValueError(
                f"tried to append {len(signals)} Signals to a {len(self._lines)} wide bus {self.name}"
            )

        for num, signal in enumerate(signals):
            self._lines[num].append(signal)

    def __getitem__(self, key):
        if isinstance(key, str):
            item = next((x for x in self._lines if x.name == key), None)
            if item is None:
                raise KeyError(f"no net named {key} in bus {self.name}")
            return item
        return self._lines[key]

    def __len__(self):
        return len(self._lines)

    @staticmethod
    def to_int(lines, order="little"):
        bin_state = "".join(["1" if line.state else "0" for line in lines])
        if order == "little":
            # reverse the bitmap
            bin_state = bin_state[::-1]

        return int(bin_state, 2)


class Clock(threading.Thread):

    pos_edge = "pos_edge"
    neg_edge = "neg_edge"

    def __init__(self, freq=10):
        super().__init__(target=self.run)
        self.freq = freq
        self._stop_event = threading.Event()
        self.handlers = {self.pos_edge: [], self.neg_edge: []}
        self.missed_ticks = 0
        self.past_runtimes = deque(maxlen=30)
        self.past_runtimes.append(time.perf_counter())
        self.max_freq = -1

    @property
    def tick_duration(self):
        return 1 / self.freq

    def start(self):
        self._stop_event.clear()
        self.run()

    def stop(self):
        self._stop_event.set()

    def every(self, edge):
        def decorator(handler):
            if edge not in self.handlers:
                raise ValueError("unknown clock edge name")

            self.handlers[edge].append(handler)
            return handler

        return decorator

    def tick(self, edge):
        for handler in self.handlers[edge]:
            handler()

    def run(self):
        edge = Clock.pos_edge
        while not self._stop_event.is_set():
            start_time = time.perf_counter()
            self.tick(edge)
            edge = Clock.pos_edge if edge == Clock.neg_edge else Clock.neg_edge
            update_duration = time.perf_counter() - start_time

            self.past_runtimes.append(update_duration)

            # calculate the maximum frequency we could run at based on the past ticks
            self.max_freq = 1/max(self.past_runtimes)

            # wait a half cycle before updating with the different edge
            #print(update_duration)
            pause = (self.tick_duration / 2) - update_duration
            if pause > 0:
                time.sleep(pause)
            else:
                self.missed_ticks += 1

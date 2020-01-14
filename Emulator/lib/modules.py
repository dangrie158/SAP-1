from .simulation import Clock, Signal, State
from .chips import *


class DataRegister:
    def __init__(self, name, databus, clk, load, clr, out):
        lower_nibble = SN74LS173(
            f"{name}:IC2",
            d=databus[:4],
            clk=clk,
            m=Signal.GND,
            n=Signal.GND,
            g1=load,
            g2=load,
            clr=clr,
        )
        upper_nibble = SN74LS173(
            f"{name}:IC3",
            d=databus[4:],
            clk=clk,
            m=Signal.GND,
            n=Signal.GND,
            g1=load,
            g2=load,
            clr=clr,
        )
        buffer = SN74LS245(
            f"{name}:IC1", a=lower_nibble.q + upper_nibble.q, dir=Signal.VCC, g=out
        )
        databus.append(buffer.b)
        self.contents = lower_nibble.q + upper_nibble.q


class InstructionRegister:
    def __init__(self, name, databus, clk, load, clr, out):
        parameter_register = SN74LS173(
            f"{name}:IC2",
            d=databus[:4],
            clk=clk,
            m=Signal.GND,
            n=Signal.GND,
            g1=load,
            g2=load,
            clr=clr,
        )
        opcode_register = SN74LS173(
            f"{name}:IC3",
            d=databus[4:],
            clk=clk,
            m=Signal.GND,
            n=Signal.GND,
            g1=load,
            g2=load,
            clr=clr,
        )
        buffer = SN74LS245(
            f"{name}:IC1", a=parameter_register.q + ([Signal.GND] * 4), dir=Signal.VCC, g=out
        )

        databus.append(buffer.b)
        self.opcode = opcode_register.q
        self.parameter = parameter_register.q
        self.contents = parameter_register.q + opcode_register.q


class MemoryAddressRegister:
    def __init__(self, name, databus, clk, load, clr):
        address_register = SN74LS173(
            f"{name}:IC2",
            d=databus[:4],
            clk=clk,
            m=Signal.GND,
            n=Signal.GND,
            g1=load,
            g2=load,
            clr=clr,
        )

        self.address = address_register.q


class FlagsRegister:
    def __init__(self, name, carry, zero, clk, load, clr):
        data_in = [carry, zero] + [Signal.GND] * 2
        address_register = SN74LS173(
            f"{name}:IC2",
            d=data_in,
            clk=clk,
            m=Signal.GND,
            n=Signal.GND,
            g1=load,
            g2=load,
            clr=clr,
        )

        self.CF = address_register.q[0]
        self.ZF = address_register.q[1]


class ALU:
    def __init__(self, name, databus, operand_1, operand_2, su, out):
        # calculate the ones complement of the second operand if the sub signal is high
        ones_complementor_1 = SN74LS86(f"{name}:IC3", a=operand_2[:4], b=[su] * 4)
        ones_complementor_2 = SN74LS86(f"{name}:IC4", a=operand_2[4:], b=[su] * 4)

        adder_1 = SN74LS283(
            f"{name}:IC1", a=operand_1[:4], b=ones_complementor_1.z, c0=su
        )
        adder_2 = SN74LS283(
            f"{name}:IC2", a=operand_1[4:], b=ones_complementor_2.z, c0=adder_1.c4
        )

        buffer = SN74LS245(
            f"{name}:IC5", a=adder_1.e + adder_2.e, dir=Signal.VCC, g=out
        )
        databus.append(buffer.b)

        zero_detect_nor = SN74LS02(
            f"{name}:IC6",
            a=[adder_1.e[0], adder_1.e[2], adder_2.e[0], adder_2.e[2]],
            b=[adder_1.e[1], adder_1.e[3], adder_2.e[1], adder_2.e[3]],
        )

        zero_detect_and = SN74LS08(
            f"{name}:IC7",
            a=[zero_detect_nor.z[0], zero_detect_nor.z[2], Signal.GND, Signal.GND],
            b=[zero_detect_nor.z[1], zero_detect_nor.z[3], Signal.GND, Signal.GND],
        )

        zero_detect_and.a[2] = zero_detect_and.z[0]
        zero_detect_and.b[2] = zero_detect_and.z[1]

        self.zero = Signal(f"{name}:ZERO", zero_detect_and.z[2])
        self.carry = Signal(f"{name}:CARRY", adder_2.c4)
        self.contents = adder_1.e + adder_2.e


class RAM:
    def __init__(self, name, databus, address, clk, load, out):

        we_inverter = SN74LS00(
            "IC9", a=[load] + [Signal.GND] * 3, b=[clk] + [Signal.GND] * 3
        )

        self.ram_1 = SN74LS189(
            f"{name}:IC1", a=address, d=databus[:4], cs=Signal.GND, we=we_inverter.z[0]
        )
        self.ram_2 = SN74LS189(
            f"{name}:IC2", a=address, d=databus[4:], cs=Signal.GND, we=we_inverter.z[0]
        )

        inverter_1 = SN74LS04(f"{name}:IC4", a=self.ram_1.o[:] + [Signal.GND] * 2)
        inverter_2 = SN74LS04(f"{name}:IC5", a=self.ram_2.o[:] + [Signal.GND] * 2)

        buffer = SN74LS245(
            f"{name}:IC3", a=inverter_1.z[:4] + inverter_2.z[:4], dir=Signal.VCC, g=out
        )
        databus.append(buffer.b)

        self.data = inverter_1.z[:4] + inverter_2.z[:4]


    @property
    def contents(self):
        contents = []
        for addr in range(16):
            # re-inverse bit order again
            low_nibble = int(format(self.ram_1.contents[addr], '04b')[::-1], 2)
            high_nibble = int(format(self.ram_2.contents[addr], '04b')[::-1], 2)

            byte = low_nibble | (high_nibble << 4)
            
            contents.append(byte)

        return contents

    @contents.setter
    def contents(self, contents):
        for addr, byte in enumerate(contents):
            # inverse bit order
            parameter = int(format(byte & 0x0F, '04b')[::-1], 2)
            instruction = int(format((byte & 0xF0) >> 4, '04b')[::-1], 2)
            self.ram_1.contents[addr] = parameter
            self.ram_2.contents[addr] = instruction

class ProgramCounter:
    def __init__(self, name, databus, enable, clk, load, clr, out):

        self.counter = SN74LS161(
            f"{name}:IC1",
            a=databus[:4],
            clk=clk,
            enp=enable,
            ent=enable,
            ld=load,
            clr=clr,
        )

        buffer = SN74LS245(
            f"{name}:IC2", a=self.counter.q[:] + [Signal.GND] * 4, dir=Signal.VCC, g=out
        )

        databus.append(buffer.b)
        self.value = self.counter.q


class InstructionDecoder:
    def __init__(
        self,
        name,
        microcode_rom,
        control_word,
        instruction,
        clear_flag,
        zero_flag,
        clk,
        clr,
    ):

        microinstruction_counter = SN74LS161(
            f"{name}:IC5",
            a=[Signal.GND] * 4,
            clk=clk,
            enp=Signal.VCC,
            ent=Signal.VCC,
            ld=Signal.VCC,
            clr=clr,
        )


        microinstruction_decoder = SN74LS138(
            a=microinstruction_counter.q[:3],
            g1=Signal.VCC,
            g2a=Signal.GND,
            g2b=Signal.GND,
        )

        self.microinstruction = Bus(("Microinstruction", [f'T{x}' for x in range(5)]), 5)
        self.microinstruction.append(microinstruction_decoder.y[:5])

        reset_nor = SN74LS00("IC7")
        # the 6th step should reset the counter (5 actual microsteps)
        #reset_nor.a[2] = State.HIGH#microinstruction_decoder.y[5]
        microinstruction_decoder.y[3].on_change(lambda ns: microinstruction_counter.clear() if not ns else None)
        # also, the inverted clear should reset
        reset_nor.b[2] = clr

        # invert the  active low reset signal
        reset_nor.a[3] = reset_nor.z[2]
        reset_nor.b[3] = reset_nor.z[2]
        microinstruction_counter.clr = reset_nor.z[3]

        self.microcode_rom1 = AT28C16(
            "IC1",
            microcode_rom,
            a=microinstruction_counter.q[:3]
            + instruction
            + [
                Signal.GND,  # chip select pin for lower CW byte
                clear_flag,
                zero_flag,
                Signal.GND,
            ],
            we=Signal.VCC,
            oe=Signal.GND,
            ce=Signal.GND,
        )

        microcode_rom2 = AT28C16(
            "IC2",
            microcode_rom,
            a=microinstruction_counter.q[:3]
            + instruction
            + [
                Signal.VCC,  # chip select pin for upper CW byte
                clear_flag,
                zero_flag,
                Signal.GND,
            ],
            we=Signal.VCC,
            oe=Signal.GND,
            ce=Signal.GND,
        )

        # create a bus with a positive logic fpr the control word,
        # to make for easier debugging
        self.control_word_positive_logic = Bus(
            ("CWP", [line.name for line in control_word._lines]), 16
        )
        self.control_word_positive_logic.append(
            self.microcode_rom1.d[:] + microcode_rom2.d[:]
        )

        cw_inverter_1 = SN74LS04("IC3")
        cw_inverter_2 = SN74LS04("IC4")

        cw_inverter_1.a[0] = self.microcode_rom1.d[1]
        cw_inverter_1.a[1] = self.microcode_rom1.d[2]
        cw_inverter_1.a[2] = self.microcode_rom1.d[4]
        cw_inverter_1.a[3] = self.microcode_rom1.d[5]
        cw_inverter_1.a[4] = self.microcode_rom1.d[6]
        cw_inverter_1.a[5] = self.microcode_rom1.d[7]
        cw_inverter_2.a[0] = microcode_rom2.d[0]
        cw_inverter_2.a[1] = microcode_rom2.d[2]
        cw_inverter_2.a[2] = microcode_rom2.d[5]
        cw_inverter_2.a[3] = microcode_rom2.d[6]
        cw_inverter_2.a[4] = microcode_rom2.d[7]
        cw_inverter_2.a[5] = Signal.GND

        control_word.append(
            [
                self.microcode_rom1.d[0],  # HLT
                cw_inverter_1.z[0],  # MI
                cw_inverter_1.z[1],  # RO
                self.microcode_rom1.d[3],  # RI
                cw_inverter_1.z[2],  # IO
                cw_inverter_1.z[3],  # II
                cw_inverter_1.z[4],  # AO
                cw_inverter_1.z[5],  # AI
                cw_inverter_2.z[0],  # EO
                microcode_rom2.d[1],  # SU
                cw_inverter_2.z[1],  # BI
                microcode_rom2.d[3],  # OI
                microcode_rom2.d[4],  # CE
                cw_inverter_2.z[2],  # CO
                cw_inverter_2.z[3],  # JP
                cw_inverter_2.z[4],  # FI
            ]
        )

class OutputDisplay():
    def __init__(
        self,
        name,
        databus,
        clk,
        load,
        clr
    ):

        # and gate is used to syncronize the loading with the clock signal
        clk_sync = SN74LS08("IC2", a=[clk] + [Signal.GND] * 3, b=[load] + [Signal.GND] * 3)
        clk.on_change(lambda x: clk_sync.z[0].notify())

        register = SN74LS273(
            f"{name}:IC3",
            d=databus,
            clk=clk_sync.z[0],
            clr=clr
        )

        self.contents = register.q
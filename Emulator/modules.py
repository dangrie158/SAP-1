from simulation import Clock, Signal, State
from chips import *


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
        parameter = SN74LS173(
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
            f"{name}:IC1", a=parameter.q + ([Signal.GND] * 4), dir=Signal.VCC, g=out
        )

        databus.append(buffer.b)
        self.opcode = opcode_register.q


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

class RAM:
    def __init__(self, name, databus, address, load, out):
        
        ram_1 = SN74LS189(f"{name}:IC1", a=address, d=databus[:4], cs=Signal.GND, we=load)
        ram_2 = SN74LS189(f"{name}:IC2", a=address, d=databus[4:], cs=Signal.GND, we=load)

        inverter_1 = SN74LS04(f"{name}:IC4", a=ram_1.o[:] + [Signal.GND]*2)
        inverter_2 = SN74LS04(f"{name}:IC5", a=ram_2.o[:] + [Signal.GND]*2)

        buffer = SN74LS245(
            f"{name}:IC3", a=inverter_1.z[:4] + inverter_2.z[:4], dir=Signal.VCC, g=out
        )
        databus.append(buffer.b)

class ProgramCounter:
    def __init__(self, name, databus, enable, clk, load, clr, out):

        counter = SN74LS161(f"{name}:IC1", a=databus[:4], clk=clk, enp=enable, ent=enable, ld=load, clr=clr)
        
        buffer = SN74LS245(
            f"{name}:IC2", a=counter.q[:] + [Signal.GND] * 4, dir=Signal.VCC, g=out
        )

        databus.append(buffer.b)
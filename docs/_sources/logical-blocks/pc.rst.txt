====================
Program Counter (PC)
====================
The program counter contains the RAM address of the next instruction to
execute.

Mode of Operation
=================
The PC is 0-initialized, thus the first instruction executed after a reset
is always at RAM byte 0.
For the counter, a `SN74LS161 <http://www.ti.com/lit/ds/symlink/sn74ls161a.pdf>`_
*4-bit syncronous counter* IC is used.

Count increment
+++++++++++++++
The counter will increment it's value whenever a clock pulse occurs while the
:math:`\mathrm{{ENABLE}` line is active.
This normally happens as the second microinsruction in a FETCH cycle as
described in the `ISA <../isa.html>`_ section.

Count Set
+++++++++
The current value can be loaded from the databus by enabling the
active-low :math:`\mathrm{\overline{LOAD}}` line which sets the counter
to the lower nibble of the databus on the next clock cycle.
This can be used to set the address of the next instruction and thus
implementing a JUMP instruction.

To enable writing the current counter's value to the DB, another
`74LS245 <http://www.ti.com/lit/ds/symlink/sn54ls245-sp.pdf>`_
*Octal Bus Tranciever* is used as a buffer.

Schematic
=========
.. figure:: images/pc.png

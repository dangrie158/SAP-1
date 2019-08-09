====================
Output Display (OUT)
====================
The output display can load the contents of the databus and
display it as a decimal integer on the 4x 7-segment displays.

It supports the display of either a unsigned :math:`\left[ 0, 255\right]`
or 2s-complement signed :math:`\left[ -128, 127\right]` 8-bit value.

Mode of Operation
=================
The value to display is read from the databus and saved in a
`SN74LS273 <https://www.ti.com/lit/ds/symlink/sn54ls273-sp.pdf>`_
*octal d-type flip-flop* on a riding clock edge when the
:math:`LOAD` signal is active.
Due to the lack of an enable pin on the register IC, the load signal is
implemented by ANDing the :math:`CLK` and :math:`LOAD` signal.

BCD decoder
+++++++++++
The decoding of the binary display is implemented as a lookup table (LUT)
using a `28C16 <http://cva.stanford.edu/classes/cs99s/datasheets/at28c16.pdf>`_
*2K x 8-bit parallel EEPROM*.
This IC has 11 address pins :math:`A_0-A_{10}` of which the first 8 are used to
input the display-value.
The next 2 address bits are used to select the digit of the display currently
active.
This leaves the last address pin to select the display mode (unsigned or
signed) using :math:`\mathrm{OUT\colon S_3}`.

Digit multiplexing
++++++++++++++++++
Since the EEPROM decoder can only drive a single digit at any time with it's 8
output lines, the 4 digits need to be multiplexed.
This is done by sequentially driving the common-cathode pin of each digit low
while simultaneously setting the :math:`A_8` and :math:`A_9` address pins of
the EEPROM which in turn will drive the anodes of the selected display digit
to the apropriate value.

The binary digit select signal that drives the address lines is implemented
by a single `SN74LS76 <http://www.ti.com/lit/ds/symlink/sn54ls76a.pdf>`_
*dual J-K flip flop* IC to implement a 2 bit binary counter.
This counter is driven by an astable `LM555 <http://www.ti.com/lit/gpn/lm555>`_
oscillator that runs fast enough to cycle through the digits without
perceivable flickering:

.. math::

   {f}_{out} &= \frac{1.44}{\mathrm{OUT\colon R_1} + 2* \mathrm{OUT\colon R3}) * \mathrm{OUT\colon C_7}} \\
   {f}_{out} &= \frac{1.44}{201kΩ * 10nF} \\
   {f}_{out} &= ~716Hz

.. math::

   {f}_{multiplex} &= \frac{{f}_{out}}{4} \\
   {f}_{multiplex} &= ~179Hz

The bianry coded digit select signal is then decoded using a
`SN74LS139 <http://www.ti.com/lit/ds/symlink/sn54ls139a-sp.pdf>`_
*2-line to 4-line decoder with active low outputs* to drive the cathodes.

Schematic
=========
.. figure:: images/out.png

===============
Hardware Blocks
===============
The SAP-1 Processor can logically be grouped into the following
submodules.

.. toctree::
   :maxdepth: 1

   logical-blocks/clk
   Data Register A <logical-blocks/datareg>
   Data Register B <logical-blocks/datareg>
   Instruction Register <logical-blocks/datareg>
   logical-blocks/alu
   logical-blocks/ram
   logical-blocks/mar
   logical-blocks/pc
   logical-blocks/out
   logical-blocks/id
   logical-blocks/sr

The individual modules communicate over the 8-bit Data Bus and
are controlled by the control lines in the Control Word.
Other than that, the only shared signals between modules are the
global clock (CLK and its inverse !CLK), and the clear signal (CLR and !CLR).

The block diagram shows how the modules are connected together.
The 8-bit bus in the middle is the databus, while the blue line
on the outside is the control word with 16 control lines.

.. figure:: logical-blocks/images/block-diagram.png

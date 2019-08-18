from lib.sap1 import SAP1
from lib.display import multisegment_number
from lib.simulation import Clock

simulation_clock = Clock(freq=5)

processor = SAP1(simulation_clock)

processor.load_program("Example-Programs/Counter.s")
simulation_clock.run()
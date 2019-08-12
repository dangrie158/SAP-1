.data:
0xF: 0x1        # step size for counter

count_up:       # begin count up routine
OUT             # output current value of register A
ADD 0xF         # add the data from RAM address 15 to RA, store the result in RA
JC count_down   # if addition has overflown the result, jump to count down routine
JMP count_up    # repeat count up routine

count_down:     # begin count down routine
SUB 0xF         # substract the step size from RA
OUT             # display the value currently in RA
JZ count_up     # jump back to count up routine if reached zero
JMP count_down  # repeat count down routine
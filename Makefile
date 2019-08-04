PYTHON = python3
PROGRAMMER_PORT = /dev/tty.wchusbserial*

LUTs/outputdecoder.bin: Spec/lut_outputdecoder.py
	$(PYTHON) Spec/lut_outputdecoder.py > $@

LUTs/microcode.bin: Spec/lut_microcode.py
	$(PYTHON) Spec/lut_microcode.py > $@

luts: LUTs/outputdecoder.bin LUTs/microcode.bin

program_lut: $(file)
	eepro -cwvf $(file) --port $(PROGRAMMER_PORT) --size=2048

clean:
	-rm LUTs/outputdecoder.bin
	-rm LUTs/microcode.bin

.PHONY: luts clean
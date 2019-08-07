PYTHON = python3
PROGRAMMER_PORT = /dev/tty.wchusbserial*

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = Docs-Src
BUILDDIR      = docs

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

docs:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	touch "$(BUILDDIR)/.nojekyll"

livedocs:
	sphinx-autobuild -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: luts clean docs livedocs
PYUIC=pyuic
.SUFFIXES: .py .ui

.ui.py:
	@echo Uic\'in $<
	@$(PYUIC) $< > $@

all: albumart_dialog_base.py \
     albumart_configuration_dialog_base.py

PYUIC=pyuic
.SUFFIXES: .py .ui

.ui.py:
	@$(PYUIC) $< > $@

all: albumart_dialog_base.py \
     albumart_configuration_dialog_base.py

albumart_dialog_base.py: albumart_dialog_base.ui

albumart_configuration_dialog_base.py: albumart_configuration_dialog_base.ui

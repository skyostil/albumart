PYUIC=pyuic
.SUFFIXES: .py .ui

.ui.py:
	@echo Uic\'in $<
	@$(PYUIC) $< > $@

all: albumart_dialog_base.py \
     albumart_configuration_dialog_base.py \
     albumart_about_dialog_base.py \
     albumart_exception_dialog_base.py \
     albumart_string_list_widget_base.py \
     albumart_progress_widget.py


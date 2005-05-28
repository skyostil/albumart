#
# Makefile for the album cover art downloader
#

all: uifiles

uifiles:
	@cd lib/albumart; for f in *.ui; do $(MAKE) -s -W "$$f"; done; cd ../..
.PHONY: uifiles


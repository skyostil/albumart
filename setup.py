# -*- coding: iso-8859-1 -*-

from distutils.core import setup
import os
import sys
import glob

setup(
	name="albumart", 
	author="Sami Kyöstilä", 
	author_email="skyostil@kempele.fi",
	contact="Sami Kyöstilä", 
	contact_email="skyostil@kempele.fi",
	url="http://kempele.fi/~skyostil/projects/albumart",
	version="1.5.0",
	license="GPL",
	description="Downloads album cover images semi-automatically from the Internet.",
	long_description="Album Cover Art Downloader is a utility for semi-automatically downloading matching cover images from Amazon.com for each album in your music collection. It saves the cover images so that they will be automatically used by programs such as Konqueror, various XMMS plugins, Windows Media Player, etc.",

        scripts = None,
	data_files=[
		('bin',['bin/albumart-qt']),
		('share/applnk/Multimedia',['share/applnk/Multimedia/albumart.desktop']),
		('share/apps/konqueror/servicemenus',['share/apps/konqueror/servicemenus/albumart_set_cover_image.desktop']),
		('share/pixmaps',['share/albumart/albumart.png']),
		('lib/albumart', glob.glob("lib/albumart/*.py")),
		('lib/albumart/id3',[
			'lib/albumart/id3/__init__.py',
			'lib/albumart/id3/binfuncs.py',
			'lib/albumart/id3/ID3v2Frames.py',
		]),
		('share/doc/albumart', ['README', 'TODO', 'CHANGELOG']),
	]
)


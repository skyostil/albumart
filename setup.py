# -*- coding: iso-8859-1 -*-

from distutils.core import setup
import os
import sys

if os.name=='nt':
	import py2exe
        scr=['bin/albumart-qt']
else:
        scr=None

setup(
	name="albumart", 
	author="Sami Kyöstilä", 
	author_email="skyostil@kempele.fi",
	contact="Sami Kyöstilä", 
	contact_email="skyostil@kempele.fi",
	url="http://kempele.fi/~skyostil/projects/albumart",
	version="1.3",
	license="GPL",
	description="Downloads album cover images semi-automatically from the Internet.",
	long_description="Album Cover Art Downloader is a utility for semi-automatically downloading matching cover images from Amazon.com for each album in your music collection. It saves the cover images so that they will be automatically used by programs such as Konqueror, various XMMS plugins, Windows Media Player, etc.",

        console=['bin/albumart-qt'],
        scripts=scr,
#	scripts=[
#		'bin/albumart-qt',
#		],
	data_files=[
		('bin',['bin/albumart-qt']),
		('share/albumart',[
			'share/albumart/cover.png',
			'share/albumart/nocover.png',
			'share/albumart/fileopen.png',
			'share/albumart/exit.png',
			'share/albumart/icon.png',
			'share/albumart/reload.png',
			'share/albumart/1rightarrow.png',
			'share/albumart/1leftarrow.png',
			'share/albumart/download.png',
			'share/albumart/filesave.png',
			]),
		('share/applnk/Multimedia',['share/applnk/Multimedia/albumart.desktop']),
		('share/apps/konqueror/servicemenus',['share/apps/konqueror/servicemenus/albumart_set_cover_image.desktop']),
		('share/pixmaps',['share/pixmaps/albumart.png']),
		('lib/albumart',[
			'lib/albumart/albumart.py',
			'lib/albumart/albumartdialog.py',
			'lib/albumart/albumartdialog_qt230.py',
			'lib/albumart/albumartdialog_qt300.py',
			'lib/albumart/amazon.py',
			'lib/albumart/version.py',
			'lib/albumart/config.py',
			'lib/albumart/albumart_source_amazon.py',
			'lib/albumart/albumart_target_freedesktop.py',
			'lib/albumart/albumart_target_windows.py',
			'lib/albumart/albumart_target_id3v2.py',
		]),
		('share/doc/albumart', ['README','TODO','CHANGELOG']),
	]
)


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
	version="1.1",
	license="GPL",
	description="Downloads album cover images semi-automatically from the Internet.",
	long_description="Album Cover Art Downloader is a download utility for semi-automatically downloading matching cover images from Amazon.com for each album in your music collection. It saves the cover images so that they will be automatically used by programs such as Konqueror, various XMMS plugins, Windows Media Player, etc.",

        scripts=scr,
#	scripts=[
#		'bin/albumart-qt',
#		],
	data_files=[
		('bin',['bin/albumart-qt']),
		('share/albumart',['share/albumart/cover.png','share/albumart/nocover.png']),
		('share/applnk/Multimedia',['share/applnk/Multimedia/albumart.desktop']),
		('share/pixmaps',['share/pixmaps/albumart.png']),
		('lib/albumart',[
			'lib/albumart/albumart.py',
			'lib/albumart/albumartdialog.py',
			'lib/albumart/albumartdialog_qt230.py',
			'lib/albumart/albumartdialog_qt300.py',
			'lib/albumart/amazon.py',
			'lib/albumart/version.py',
		]),
		('share/doc/albumart', ['README','TODO']),
	]
)


from distutils.core import setup
import os
import sys

if os.name=='nt':
	import py2exe

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
	scripts=[
		'bin/albumart-qt.py',
		],
	data_files=[
		('share/albumart',['share/albumart/cover.png','share/albumart/nocover.png']),
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


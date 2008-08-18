# -*- coding: iso-8859-1 -*-

from distutils.core import setup
import os
import sys
import glob

sys.path.append("lib/albumart")
import version

# Make sure all the files are up to date.
# This is somewhat of a hack but it works.
if len(sys.argv) > 1:
  for arg in sys.argv:
    if arg[0] == "-" and "help" in arg or arg == "-h":
      break
  else:
    os.system("make")

setup(
	name="albumart", 
	author="Sami Kyöstilä", 
	author_email="sami.kyostila@gmail.com",
	contact="Sami Kyöstilä", 
	contact_email="sami.kyostila@gmail.com",
	url="http://unrealvoodoo.org/hiteck/projects/albumart",
	version=version.__version__,
	license="GPL",
	description="Downloads album cover images semi-automatically from the Internet.",
	long_description="Album Cover Art Downloader is a utility for semi-automatically downloading matching cover images for each album in your music collection. It saves the cover images so that they will be automatically used by programs such as Konqueror, various XMMS plugins, Windows Media Player, etc.",

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
		('lib/albumart/yahoo',[
			'lib/albumart/yahoo/__init__.py',
		]),
		('lib/albumart/yahoo/search',[
			'lib/albumart/yahoo/search/domparsers.py',
			'lib/albumart/yahoo/search/debug.py',
			'lib/albumart/yahoo/search/__init__.py',
			'lib/albumart/yahoo/search/webservices.py',
			'lib/albumart/yahoo/search/version.py',
		]),
		('share/doc/albumart', ['README', 'TODO', 'CHANGELOG']),
	]
)


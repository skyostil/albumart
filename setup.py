from distutils.core import setup
import os

if os.name=='nt':
	import py2exe

setup(name="albumart", scripts=['albumart-qt.py'])


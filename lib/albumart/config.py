# -*- coding: iso-8859-1 -*-

import ConfigParser
import os

def getConfigPath(appname):
	"""Returns a path that holds the configuration for the application."""
	if appname:
		if os.name=="posix":
			path = os.path.expanduser("~/." + appname)
			try:
				os.mkdir(path)
			except:
				pass
			return path
		elif os.name=="nt":
			try:
				path = os.path.join(os.environ["APPDATA"], appname)
				try:
					os.mkdir(path)
				except:
					pass
				return path
			except:
				pass
	return None

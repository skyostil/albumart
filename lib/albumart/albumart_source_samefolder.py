# -*- coding: iso-8859-1 -*-
import urllib
import glob
import albumart
import tempfile

defaultConfig = {
	"enabled":		1,
}

configDesc = {
	"enabled":		("boolean", "Use images found in the same folder"),
}

class SameFolder(albumart.Source):
	"""Look for images in the same folder."""
	def __init__(self):
		self.configure(defaultConfig)
		self.ignoredFiles = [
			"folder.jpg"
		]

	def configure(self, config):
		self.enabled = config["enabled"]

	def findAlbum(self,name):
		print path
		return path

	def getCover(self,album):
		if self.enabled:
			for f in glob.glob(os.path.join(path, "*.jpg")):
				print f
				
				if os.path.basename(f) in self.ignoredFiles:
					continue
					
				try:
					file = open(f, "rb")
					output = tempfile.mktemp(".jpg")
					o = open(output, "wb")
					o.write(file)
					o.close()
					return output
				except:
					pass

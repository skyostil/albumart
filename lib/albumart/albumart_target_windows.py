# -*- coding: iso-8859-1 -*-
import albumart
import Image
import os

defaultConfig = {
	"enabled":	1,
	"filename":	"folder.jpg",
}

configDesc = {
	"enabled":	("boolean", "Set image for Windows"),
}

class Windows(albumart.Target):
	"""Windows XP(tm) Explorer."""
	def __init__(self):
		self.configure(defaultConfig)

	def configure(self, config):
		self.filename = config["filename"]
		self.enabled = config["enabled"]

	def getCover(self, path):
		if self.enabled:
			if self.hasCover(path):
				return os.path.join(path,self.filename)

	def setCover(self, path, cover):
		if self.enabled:
			i = Image.open(cover)
			i.save(os.path.join(path, self.filename), "JPEG")

	def hasCover(self, path):
		if self.enabled:
			return os.path.isfile(os.path.join(path,self.filename))
		return 0

# -*- coding: iso-8859-1 -*-
import albumart
import Image
import os

class Windows(albumart.Target):
	"""Windows XP(tm) Explorer."""
	def __init__(self, config=None):
		self.config = config
		if config:
			if config.has_section("Windows"):
				self.filename = config.get("Windows", "filename")
				self.enabled = config.getboolean("Windows", "enabled")
			else:
				self.filename = "folder.jpg"
				self.enabled = 1
				config.add_section("Windows")
				config.set("Windows", "enabled", "yes")
				config.set("Windows", "filename", self.filename)

	def getCover(self, path):
		if not self.enabled: return
		if self.hasCover(path):
			return os.path.join(path,self.filename)

	def setCover(self, path, cover):
		if not self.enabled: return
		i = Image.open(cover)
		i.save(os.path.join(path, self.filename), "JPEG")

	def hasCover(self, path):
		if not self.enabled: return 0
		return os.path.isfile(os.path.join(path,self.filename))

	def setEnabled(self, enabled):
		self.enabled = enabled
		if self.config:
			self.config.set("Windows", "enabled", str(enabled))

# -*- coding: iso-8859-1 -*-
import albumart
import Image
import ConfigParser
import os

defaultConfig = {
	"enabled":	1,
	"filename":	".folder.png",
}

configDesc = {
	"enabled":	("boolean", "Set image for Freedesktop (KDE, Gnome, etc.)"),
}

# A wrapper around a file to work around the fact that
# ConfigParser writes keys in lowercase.
class MyWriter(file):
	def write(self,data):
		if data.startswith("icon ="):
			data = "Icon =" + data[6:]
		file.write(self,data)

class Freedesktop(albumart.Target):
	"""Freedesktop.org's desktop file standard (for KDE, GNOME, etc.)"""
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
		if not self.enabled: return

		i = Image.open(cover)
		i.save(os.path.join(path, self.filename), "PNG")

		# .directory-file entry
		cf=ConfigParser.ConfigParser()
		try:
			cf.read(os.path.join(path,".directory"))
		except:
			pass
		if not cf.has_section("Desktop Entry"):
			cf.add_section("Desktop Entry")
		cf.set("Desktop Entry", "Icon", os.path.join(path, self.filename))
		w=MyWriter(os.path.join(path,".directory"),"w")
		cf.write(w)

	def removeCover(self, path):
		if not self.enabled: return
		os.unlink(os.path.join(path, self.filename))

	def hasCover(self, path):
		if self.enabled:
			return os.path.isfile(os.path.join(path,self.filename))

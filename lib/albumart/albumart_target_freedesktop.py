# -*- coding: iso-8859-1 -*-
import albumart
import Image
import ConfigParser
import os

# A wrapper around a file to work around the fact that
# ConfigParser writes keys in lowercase.
class MyWriter(file):
	def write(self,data):
		if data.startswith("icon ="):
			data = "Icon =" + data[6:]
		file.write(self,data)

class Freedesktop(albumart.Target):
	"""Freedesktop.org's desktop file standard (for KDE, GNOME, etc.)"""
	def __init__(self, config=None):
		self.config = config
		if config:
			if config.has_section("Freedesktop"):
				self.filename = config.get("Freedesktop", "filename")
				self.enabled = config.getboolean("Freedesktop", "enabled")
			else:
				self.filename = ".folder.png"
				self.enabled = 1
				config.add_section("Freedesktop")
				config.set("Freedesktop", "enabled", "yes")
				config.set("Freedesktop", "filename", self.filename)

	def getCover(self, path):
		if not self.enabled: return
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

	def hasCover(self, path):
		if not self.enabled: return 0
		return os.path.isfile(os.path.join(path,self.filename))

	def setEnabled(self, enabled):
		self.enabled = enabled
		if self.config:
			self.config.set("Freedesktop", "enabled", str(enabled))

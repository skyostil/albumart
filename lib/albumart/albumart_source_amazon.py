# -*- coding: iso-8859-1 -*-
import urllib
import amazon
import albumart
import tempfile

class Amazon(albumart.Source):
	"""Amazon.com album cover source."""
	def __init__(self, config=None):
		self.config = config
		if config:
			if config.has_section("Amazon"):
				self.enabled = config.getboolean("Amazon", "enabled")
				try:
					l = config.get("Amazon", "licenseNumber")
					if l and len(l):
						amazon.setLicense(l)
				except:
					pass
			else:
				self.enabled = 1
				config.add_section("Amazon")
				config.set("Amazon", "enabled", "yes")
				config.set("Amazon", "licenseNumber", "")

	def findAlbum(self,name):
		if not self.enabled: return
		try:
			return amazon.searchByKeyword(name,type="lite",product_line="music")
		except amazon.AmazonError:
			pass

	def getCover(self,album):
		if not self.enabled: return
		try:
			i = urllib.urlopen(album.ImageUrlLarge)
			output = tempfile.mktemp(".jpg")
			o = open(output, "wb")
			o.write(i.read())
			o.close()
			return output
		except:
			return None

	def setEnabled(self, enabled):
		self.enabled = enabled
		if self.config:
			self.config.set("Amazon", "enabled", str(enabled))

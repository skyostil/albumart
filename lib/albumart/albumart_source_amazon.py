# -*- coding: iso-8859-1 -*-
import urllib
import amazon
import albumart
import tempfile

defaultConfig = {
	"enabled":		1,
	"licensenumber":	"",
	"locale":	        "us",
}

configDesc = {
	"enabled":		("boolean", "Use Amazon as an image source"),
	"licensenumber":	("string", "Set Amazon license key...", "Please enter your Amazon Web Services license key.\nThis key can be obtained free of charge from Amazon at\nhttps://associates.amazon.com/exec/panama/associates/join/developer/application.html/ref=ac_blrb/103-0873489-2667844"),
	"locale":	        ("string", "Set Amazon country...", "Please enter the country setting for Amazon. It can be one of us, uk, de, jp."),
}

class Amazon(albumart.Source):
	"""Amazon.com album cover source."""
	def __init__(self):
		self.configure(defaultConfig)

	def configure(self, config):
		self.enabled = config["enabled"]
		l = config["licensenumber"]
		if l and len(l):
			amazon.setLicense(l)
		l = config["locale"]
		if l and len(l):
			amazon.setLocale(l)

	def findAlbum(self,name):
		if self.enabled:
			try:
				return amazon.searchByKeyword(name,type="lite",product_line="music")
			except amazon.AmazonError:
				pass

	def getCover(self,album):
		if self.enabled:
			try:
				i = urllib.urlopen(album.ImageUrlLarge)
				output = tempfile.mktemp(".jpg")
				o = open(output, "wb")
				o.write(i.read())
				o.close()
				return output
			except:
				return None

# -*- coding: iso-8859-1 -*-

"""Download covers from Amazon.com."""

import urllib
import amazon
import albumart
import tempfile

defaultConfig = {
  "enabled":        1,
  "licensenumber":  "D1ESMA5AOEZB24",
  "locale":         "us",
}

configDesc = {
  "enabled":        ("boolean", "Enable Amazon.com"),
  "locale":         ("stringlist",  "Country",
                     ["us", "uk", "de", "jp"]),
}

class Amazon(albumart.Source):
  """Amazon"""
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

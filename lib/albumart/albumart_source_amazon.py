# -*- coding: iso-8859-1 -*-

"""Download covers from Amazon.com."""

import urllib
import amazon
import albumart
import tempfile
import Image

defaultConfig = {
  "enabled":        1,
  "licensenumber":  "D1ESMA5AOEZB24",
  "locale":         "us",
  "proxy":          amazon.getProxy() or "",
  "minsize":        0
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
  "locale":         ("stringlist",  "Country",
                     ["us", "uk", "de", "jp"]),
  "proxy":          ("string",  "Proxy server"),
  "minsize":        ("integer",  "Only accept images at least this big (pixels)", (0, 1024))
}

class Amazon(albumart.Source):
  """Amazon"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.enabled = config["enabled"]
    self.minsize = config["minsize"]
    l = config["licensenumber"]
    if l and len(l):
      amazon.setLicense(l)
    l = config["locale"]
    if l and len(l):
      amazon.setLocale(l)
    l = config["proxy"]
    if l and len(l):
      amazon.setProxy(l)

  def findAlbum(self,name):
    if self.enabled:
      try:
        return amazon.searchByKeyword(name,type="lite",product_line="music")
      except amazon.AmazonError:
        pass

  def verifyCover(self, filename):
    try:
      img = Image.open(filename)
      return img.size[0] > self.minsize or img.size[1] > self.minsize
    except:
      return False

  def getCover(self, album):
    if self.enabled:
      try:
        i = urllib.urlopen(album.ImageUrlLarge)
        output = tempfile.mktemp(".jpg")
        o = open(output, "wb")
        o.write(i.read())
        o.close()
        if self.verifyCover(output):
          return output
        else:
          os.unlink(output)
          return None
      except:
        return None

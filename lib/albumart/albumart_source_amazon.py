# -*- coding: iso-8859-1 -*-
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
  "enabled":        ("boolean", "Use Amazon as an image source"),
  "locale":          ("stringlist",  "Set Amazon country...",
                                     "Please enter the country setting for Amazon.",
                                     ["us", "uk", "de", "jp"]),
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
      except amazon.NoLicenseKey, x:
        raise RuntimeError(
                "Please get a license key from http://www.amazon.com/gp/aws/registration/registration-form.html\n " +
                "and enter it into Settings | Set Amazon license key.")            

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

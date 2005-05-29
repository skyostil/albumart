# -*- coding: iso-8859-1 -*-

"""Download covers from Yahoo! Image Search"""

import urllib
from yahoo.search.webservices import ImageSearch
import albumart
import tempfile
import os

defaultConfig = {
  "enabled":        1,
  "appid":          "albumart"
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
}

class Yahoo(albumart.Source):
  """Yahoo!"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.enabled = config["enabled"]
    self.appid = config["appid"]

  def findAlbum(self, name):
    try:
      searcher = ImageSearch(self.appid)
      searcher.query = name
      searcher.results = 10
      return list(searcher.parse_results())
    except:
      pass

  def getCover(self, cover):
    if self.enabled:
      try:
        i = urllib.urlopen(cover["Url"])
        output = tempfile.mktemp(".jpg")
        o = open(output, "wb")
        o.write(i.read())
        o.close()
        return output
      except:
        return None

# -*- coding: iso-8859-1 -*-

"""Download covers from Yahoo! Image Search"""

import urllib
from yahoo.search.webservices import ImageSearch
import albumart
import tempfile
import os

defaultConfig = {
  "enabled":        0,
  "appid":          "albumart",
  "max_results":    10,
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
  "max_results":    ("integer",),
}

class Yahoo(albumart.Source):
  """Yahoo!"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.enabled = config["enabled"]
    self.appid = config["appid"]
    self.maxResults = config["max_results"]

  def findAlbum(self, artist, album):
    if self.enabled:
      try:
        searcher = ImageSearch(self.appid)
        searcher.query = artist+" "+album
        searcher.results = self.maxResults
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
        return albumart.Cover(output)
      except:
        return None

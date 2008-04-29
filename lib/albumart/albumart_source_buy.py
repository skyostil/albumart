# -*- coding: iso-8859-1 -*-

"""Download covers from Buy.com."""

import urllib
import re
import sys
import os
import tempfile
import albumart

defaultConfig = {
  "enabled":        0,
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
}


buy = {
  'search' : { 'url'   : 'http://www.buy.com/retail/searchresults.asp?',
               'query' : 'qu',
               'args'  : { 'search_store': '6', 'querytype' : 'music' },
                  're' :  [ r'<a href="/retail/product.asp\?sku=(\d+).*?">' ] },
}

class Buy(albumart.Source):
  """Buy.com"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.enabled = config["enabled"]

  def search(self, site, page, keyword):
    if self.enabled:
      s = site[page]
      args = s['args']
      args[s['query']] = keyword
      url = s['url'] + urllib.urlencode(args)

      file = urllib.urlopen(url)
      content = file.read()
      result = []
      
      for i in s['re']:
        r = re.compile(i, re.M)
        result += r.findall(content)

      return result

  def findAlbum(self, artist, album):
    if self.enabled:
      try:
        return self.search(buy, 'search', artist+" "+album)[:20]
      except:
        pass

  def getCover(self, id):
    if self.enabled:
      try:
        url = "http://ak.buy.com/db_assets/large_images/" + id[-3:] + "/" + id + ".jpg"
        i = urllib.urlopen(url)
        output = tempfile.mktemp(".jpg")
        o = open(output, "wb")
        o.write(i.read())
        o.close()
        return albumart.Cover(output)
      except:
        return None

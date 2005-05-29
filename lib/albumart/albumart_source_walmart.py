# -*- coding: iso-8859-1 -*-

"""Download covers from Walmart."""

#
# Based on code by Filip Kalinski, 2004 - filon@pld.org.pl
#

import urllib
import re
import sys
import os
import tempfile
import albumart

defaultConfig = {
  "enabled":        1,
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
}

walmart = { 'search' : { 'url'   : 'http://www.walmart.com/catalog/search-ng.gsp?',
			 'query' : 'search_query',
			 'args'  : { 'search_constraint': '4104', 'ics' : '5', 'ico': '0' },
			 're' :
			[ r'<input type="hidden" name="product_id" value="(\d+)">' ] },
            'result' : { 'url'   : 'http://www.walmart.com/catalog/product.gsp?',
	                 'query' : 'product_id',
			 'args'  : { },
			 're' :
			[ r'<a href="javascript:photo_opener\(\'(\S+.jpg)&product_id=',
			  r'<meta name="Description" content="(.+) at Wal-Mart.*">' ] }
	  }

class Walmart(albumart.Source):
  """Walmart"""
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

  def findAlbum(self, name):
    try:
      albums = self.search(walmart, 'search', name)
      return [self.search(walmart, 'result', album) for album in albums]
    except:
      pass

  def getCover(self, id):
    if self.enabled:
      try:
        url1, url2, name = id
        i = urllib.urlopen(url1)
        output = tempfile.mktemp(".jpg")
        o = open(output, "wb")
        o.write(i.read())
        o.close()
        return output
      except:
        return None

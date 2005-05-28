# -*- coding: iso-8859-1 -*-

"""Guess album and artist from the path."""

import albumart
import re
import os

# Here is the list of patterns to match against.
# You can use the following tags:
#
#   %(artist)
#   %(album)
#   %(title)
#   %(track)
#   %(year)
#   %(any)
#
# The patterns are evaluated in sequential order
# until a match is found.
PATTERNS = [
  "%(year)/%(artist)/%(album)",
  "%(year)/%(artist) - %(album)",
  "%(any)/%(year) %(artist) - %(album)",
  "%(year) %(artist) - %(album)",
  "%(any)/%(artist) - %(album)",
  "%(artist) - %(album)",
  "%(artist)/%(album)"
]

defaultConfig = {
  "enabled":        1,
  "patterns":       list(PATTERNS),
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
  "patterns":       ("stringlist", """<qt>
Here is the list of patterns to match against.
You can use the following tags:

<ul>
  <li><strong>%(artist)</strong> - Artist name</li>
  <li><strong>%(album)</strong> - Album name</li>
  <li><strong>%(title)</strong> - Song title</li>
  <li><strong>%(track)</strong> - Track number</li>
  <li><strong>%(year)</strong> - Year published</li>
  <li><strong>%(any)</strong> - Any sequence of characters</li>
</ul>
The patterns are evaluated in sequential order
until a match is found.
</qt>"""),
}

class PathRecognizer(albumart.Recognizer):
  """Path name"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.enabled = config["enabled"]
    self.patterns = config["patterns"]
    
  def patternToRegex(self, pattern):
    inTag = False
    tag = ""
    regex = ""
    
    tagRegex = {
      "artist": "([^/]+)",
      "album": "([^/]+)",
      "title": "([^/]+)",
      "track": "([0-9.]+)",
      "year": "([0-9]+)",
      "any": "(.*)",
    }
    
    key = {}
    tagCount = 1
    
    for c in pattern:
      if not inTag:
        if c == "%":
          inTag = True
          tag = ""
        else:
          regex += c
      else:
        if c != "(" and c != ")":
          tag += c
        elif c == ")":
          inTag = False
          regex += tagRegex[tag]
          key[tag] = tagCount
          tagCount += 1
    return (regex, key)
    
  def guessArtistAndAlbum(self, path):
    if not self.enabled: return (None, None)
    
    if os.path.isfile(path):
      path = os.path.dirname(path)
      
    artist = None
    album = None
    path = path.replace("\\", "/")
    # look at the last two path elements at most
    path = "/".join(path.split("/")[-2:])
      
    for p in self.patterns:
      (regex, key) = self.patternToRegex(p)
      m = re.search(regex, path)
      if m:
        try:
          artist = m.group(key["artist"])
        except KeyError:
          pass
        try:
          album = m.group(key["album"])
        except KeyError:
          pass
      if album and artist:
        break
    return (artist, album)
      
if __name__ == "__main__":
  p = PathRecognizer()
  print p.guessArtistAndAlbum("/mnt/some/path/to/music/artist/album")
  print p.guessArtistAndAlbum("2004/artist/album")
  print p.guessArtistAndAlbum("foo/2004 artist - album")
  print p.guessArtistAndAlbum("artist - album")
  print p.guessArtistAndAlbum(r"artist\album")
  print p.guessArtistAndAlbum(r"2004\artist\album")
  print p.guessArtistAndAlbum(r"foo\2004 artist - album")
  print p.guessArtistAndAlbum(r"artist - album")

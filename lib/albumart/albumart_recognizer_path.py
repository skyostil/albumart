# -*- coding: iso-8859-1 -*-
import albumart
import re
import os

defaultConfig = {
}

configDesc = {
}

# Here are the list of patterns to match against.
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
patterns = [
  "%(year)/%(artist)/%(album)",
  "%(year)/%(artist) - %(album)",
  "%(any)/%(year) %(artist) - %(album)",
  "%(year) %(artist) - %(album)",
  "%(any)/%(artist) - %(album)",
  "%(artist) - %(album)",
  "%(artist)/%(album)"
]

class PathRecognizer(albumart.Recognizer):
  """Guess album and artist from the path."""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    pass
    
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
    if os.path.isfile(path):
      path = os.path.dirname(path)
      
    artist = None
    album = None
    path = path.replace("\\", "/")
    # look at the last two path elements at most
    path = "/".join(path.split("/")[-2:])
      
    for p in patterns:
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


  
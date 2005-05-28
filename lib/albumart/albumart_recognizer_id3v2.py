# -*- coding: iso-8859-1 -*-

"""Guess album and artist from ID3v2 tags."""

import albumart
import id3   # PyID3, see http://icepick.info/projects/pyid3/
import os
import glob

defaultConfig = {
  "enabled":        1,
}

configDesc = {
  "enabled":        ("boolean", "Enable"),
}

class ID3v2Recognizer(albumart.Recognizer):
  """ID3v2 tags"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.enabled = config["enabled"]
    
  def getFileList(self, path):
    if os.path.isfile(path) and path.lower().endswith(".mp3"):
      return [path]
    return glob.glob(os.path.join(path, "*.mp3"))
    
  def guessArtistAndAlbum(self, path):
    if not self.enabled: return (None, None)
    
    artist = None
    album = None
      
    for f in self.getFileList(path):
      id3v2 = id3.ID3v2(f)
      for frame in id3v2.frames:
        if frame.id == "TALB":
          album = frame.get_value()
        elif frame.id == "TPE1":
          artist = frame.get_value()
    
      if album and artist:
        break          
    
    return (artist, album)

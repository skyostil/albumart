# -*- coding: iso-8859-1 -*-

"""Set image for Windows Media Player, Windows Explorer, etc."""

import albumart
import Image
import os

defaultConfig = {
  "enabled":   1,
  "filename":  "folder.jpg",
}

configDesc = {
  "enabled":  ("boolean", "Enable"),
  "filename": ("string", "File name for image")
}

class Windows(albumart.Target):
  """Windows Media Player"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.filename = config["filename"]
    self.enabled = config["enabled"]

  def getCover(self, path):
    if self.enabled:
      if self.hasCover(path):
        return os.path.join(path, self.filename)

  def setCover(self, path, cover):
    if self.enabled and not os.path.isfile(path):
      i = Image.open(cover)
      i.save(os.path.join(path, self.filename), "JPEG")

  def hasCover(self, path):
    if self.enabled and not os.path.isfile(path):
      return os.path.isfile(os.path.join(path,self.filename))
    return 0

  def removeCover(self, path):
    if not self.enabled or os.path.isfile(path):
      return
    
    try:
      os.unlink(os.path.join(path, self.filename))
    except OSError:
      pass

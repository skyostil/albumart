# -*- coding: iso-8859-1 -*-

"""Set image for Windows Media Player, Windows Explorer, etc."""

import albumart
import Image
import os

scales = {
  "Default": None,
  "128x128 pixels": 128,
  "64x64 pixels": 64,
  "48x48 pixels": 48,
  "32x32 pixels": 32,
}

defaultConfig = {
  "enabled":   1,
  "filename":  "folder.jpg",
  "scale":     "Default",
}

configDesc = {
  "enabled":  ("boolean", "Enable"),
  "filename": ("string", "File name for image"),
  "scale":    ("stringlist", "Image size", scales.keys())
}

class Windows(albumart.Target):
  """Windows Media Player"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.filename = config["filename"]
    self.enabled = config["enabled"]
    self.scale = scales[config["scale"]]

  def getCover(self, path):
    if self.enabled:
      if self.hasCover(path):
        return os.path.join(path, self.filename)

  def setCover(self, path, cover):
    target = os.path.join(path, self.filename)
    if self.enabled and not os.path.isfile(path) and not cover == target:
      i = Image.open(cover)

      # scale it
      if self.scale:
        i = i.resize((self.scale, self.scale), resample = 1)

      i.save(target, "JPEG")

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

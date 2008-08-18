# -*- coding: iso-8859-1 -*-

"""Save the image to an arbitrary file."""

import albumart
import Image
import os

scales = {
  "Default": None,
  "512x512 pixels": 512,
  "256x256 pixels": 256,
  "128x128 pixels": 128,
  "64x64 pixels": 64,
  "48x48 pixels": 48,
  "32x32 pixels": 32,
}

defaultConfig = {
  "enabled":   0,
  "filename":  "%(artist)_%(album).png",
  "scale":     "Default",
}

configDesc = {
  "enabled":  ("boolean", "Enable"),
  "filename": ("string", """<qt>File name for image. You can use the following tags:
<ul>
  <li><strong>%(album)</strong> - Album name</li>
  <li><strong>%(artist)</strong> - Artist name</li>
</ul>
The file extension specifies the written image format. The file name can also contain
a path.
</qt>"""),
  "scale":    ("choice", "Image size", scales.keys())
}

class Generic(albumart.Target):
  """Generic"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.filename = config["filename"]
    self.enabled = config["enabled"]
    self.scale = scales[config["scale"]]

  def getFilenameForPath(self, path):
    if not "%(" in self.filename:
      return self.filename
    (artist, album) = albumart.guessArtistAndAlbum(path)
    artist = artist or "Unknown"
    album = album or "Unknown"
    return self.filename\
      .replace("%(album)", album)\
      .replace("%(artist)", artist)

  def getCover(self, path):
    if self.enabled:
      if self.hasCover(path):
        return albumart.Cover(os.path.join(path, self.getFilenameForPath(path)))

  def setCover(self, path, cover):
    cover = cover.path
    target = os.path.join(path, self.getFilenameForPath(path))
    if self.enabled and not os.path.isfile(path) and not cover == target:
      i = Image.open(cover)

      # scale it
      if self.scale:
        i = i.resize((self.scale, self.scale), resample = 1)

      i.save(target)

  def hasCover(self, path):
    if self.enabled and not os.path.isfile(path):
      return os.path.isfile(os.path.join(path, self.getFilenameForPath(path)))
    return False

  def removeCover(self, path):
    if not self.enabled or os.path.isfile(path):
      return

    try:
      os.unlink(os.path.join(path, self.getFilenameForPath(path)))
    except OSError:
      pass

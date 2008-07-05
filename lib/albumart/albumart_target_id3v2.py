# -*- coding: iso-8859-1 -*-

"""Write images to ID3v2 tags in MP3 files."""

import albumart
import glob
import os
import id3   # PyID3, see http://icepick.info/projects/pyid3/
import tempfile
import Image

# all defined APIC picture types
pictureTypes = id3.ID3v2Frames.AttachedPicture.picturetypes

defaultConfig = {
  "enabled":      1,
  "type":          "03: " + pictureTypes[chr(3)],
}

configDesc = {
  "enabled":      ("boolean", "Enable"),
  "type":         ("choice", "Output image type",
                   ["%02X: %s" % (ord(c), d) for c, d in pictureTypes.items()]),
}

class ID3v2(albumart.Target):
  """MP3 files"""
  def __init__(self):
    self.configure(defaultConfig)
    self.tempfile = tempfile.mktemp(".jpg")

  def __del__(self):
    try:
      os.unlink(self.tempfile)
    except:
      pass

  def configure(self, config):
    self.enabled = config["enabled"]
    self.pictureType = chr(int(config["type"][:2]))

  def getCover(self, path):
    # get the first APIC cover we find
    if self.enabled:
      for f in self.getFileList(path):
        id3v2 = id3.ID3v2(f)
        try:
          for frame in id3v2.frames:
            if frame.id == "APIC":
              file = open(self.tempfile, "wb")
              file.write(frame.image)
              file.close()
              return albumart.Cover(self.tempfile)
        except:
          pass

  def setCover(self, path, cover):
    cover = cover.path
    if not self.enabled: return

    img = Image.open(cover)
    img.load()

    # scale if needed
    if self.pictureType == chr(1):
      img = img.resize((32, 32), resample = 1)

    # convert to JPEG if needed
    if img.format != "JPEG":
      img = img.convert("RGB")
      img.save(self.tempfile)
      data = open(self.tempfile, "rb").read()
    else:
      data = open(cover, "rb").read()
    errors = ""

    for f in self.getFileList(path):
      try:
        stat = os.stat(f)
        id3v2 = id3.ID3v2(f)
        frame = id3v2.get_apic_frame('Cover Image')
        frame.image = data
        frame.picturetype = self.pictureType
        if id3v2.version[1] < 4:
          frame.unsynchronisation = True
        id3v2.save()
        # restore the modification date and time
        os.utime(f, (stat.st_atime, stat.st_mtime))
      except Exception, x:
        # collect exceptions, since some of the files might work
        if len(str(x)):
          errors += "ID3v2: " + os.path.basename(f) + ": " + str(x) + "\n"

    if len(errors):
      raise UserWarning(errors)

  def getFileList(self, path):
    if os.path.isfile(path) and path.lower().endswith(".mp3"):
      return [path]
    return []

  def removeCover(self, path):
    if not self.enabled: return

    for f in self.getFileList(path):
      stat = os.stat(f)
      id3v2 = id3.ID3v2(f)

      newframes = []
      for frame in id3v2.frames:
        if frame.id != "APIC":
          newframes.append(frame)
      id3v2.frames = newframes
      id3v2.save()
      # restore the modification date and time
      os.utime(f, (stat.st_atime, stat.st_mtime))

  def hasCover(self, path):
    if self.enabled:
      for f in self.getFileList(path):
        id3v2 = id3.ID3v2(f)

        try:
          for frame in id3v2.frames:
            if frame.id == "APIC":
              return 1
        except:
          pass

# -*- coding: iso-8859-1 -*-
import albumart
import glob
import os
import id3   # PyID3, see http://icepick.info/projects/pyid3/
import tempfile
import Image

defaultConfig = {
  "enabled":      1,
}

configDesc = {
  "enabled":      ("boolean", "Save image directly into MP3 files (ID3v2 tag)"),
}

class ID3v2(albumart.Target):
  """ID3v2 APIC tag"""
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

  def getCover(self, path):
    # get the first APIC cover we find
    if self.enabled:
      for f in self.__filelist__(path):
        id3v2 = id3.ID3v2(f)

        try:
          for frame in id3v2.frames:
            if frame.id == "APIC":
              file = open(self.tempfile,"wb")
              file.write(frame.image)
              file.close()
              return self.tempfile
        except:
          pass

  def setCover(self, path, cover):
    if not self.enabled: return

    img = Image.open(cover)
    img.load()

    # convert to JPEG if needed
    if img.format != "JPEG":
      img = img.convert("RGB")
      img.save(self.tempfile)
      data = open(self.tempfile, "rb").read()
    else:
      data = open(cover, "rb").read()
    errors = ""

    for f in self.__filelist__(path):
      print f
      try:
        id3v2 = id3.ID3v2(f)
        frame = id3v2.get_apic_frame('Cover Image')
        frame.image = data
        frame.picturetype = '\x03'
        frame.unsynchronisation = True
        id3v2.save()
      except Exception,x: # collect exceptions, since some of the files might work
        if len(str(x)):
          errors += "ID3v2: " + os.path.basename(f) + ": " + str(x) + "\n"

    if len(errors):
      raise UserWarning(errors)

  def __filelist__(self, path):
    return glob.glob(os.path.join(path, "*.mp3"))

  def removeCover(self, path):
    if not self.enabled: return

    for f in self.__filelist__(path):
      id3v2 = id3.ID3v2(f)

      newframes = []
      for frame in id3v2.frames:
        if frame.id != "APIC":
          newframes.append(frame)
      id3v2.frames = newframes
      id3v2.save()

  def hasCover(self, path):
    if self.enabled:
      for f in self.__filelist__(path):
        id3v2 = id3.ID3v2(f)

        try:
          for frame in id3v2.frames:
            if frame.id == "APIC":
              return 1
        except:
          pass

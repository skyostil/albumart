# -*- coding: iso-8859-1 -*-
import albumart
import Image
import ConfigParser
import os

defaultConfig = {
  "enabled":   1,
  "relpaths":  1,
  "filename":  ".folder.png",
}

configDesc = {
  "enabled":  ("boolean", "Set image for Freedesktop (KDE, Gnome, etc.)"),
}

class MyParser(ConfigParser.ConfigParser):
  def optionxform(self, option):
    # we override this method cause we don't want lowercase options.
    return option

  def write(self, fp):
    # this is overrided to make no use of white spaces around '='.
    """Write an .ini-format representation of the configuration state."""
    if self.defaults():
      fp.write("[%s]\n" % DEFAULTSECT)
      for (key, value) in self.defaults().items():
        fp.write("%s=%s\n" % (key, str(value).replace('\n', '\n\t')))
      fp.write("\n")
    for section in self.sections():
      fp.write("[%s]\n" % section)
      for key in self.options(section):
        if key != "__name__":
          fp.write("%s=%s\n" % (key, self.get(section,key).replace('\n', '\n\t')))
    fp.write("\n")

class Freedesktop(albumart.Target):
  """Freedesktop.org's desktop file standard (for KDE, GNOME, etc.)"""
  def __init__(self):
    self.configure(defaultConfig)

  def configure(self, config):
    self.filename = config["filename"]
    self.enabled = config["enabled"]
    
    try:
      self.relpaths = (config["relpaths"] == "1")
    except:
      self.relpaths = 1

  def getCover(self, path):
    if self.enabled:
      if self.hasCover(path):
        return os.path.join(path,self.filename)

  def setCover(self, path, cover):
    if not self.enabled:
      return
    
    # check that it is not a file
    if os.path.isfile(path):
      return

    i = Image.open(cover)
    i.save(os.path.join(path, self.filename), "PNG")

    # .directory-file entry
    cf=MyParser()
    try:
      cf.read(os.path.join(path, ".directory"))
    except:
      pass
    if not cf.has_section("Desktop Entry"):
      cf.add_section("Desktop Entry")
      
    if self.relpaths or os.name == "nt":
      cf.set("Desktop Entry", "Icon", os.path.join(".", self.filename))
    else:
      cf.set("Desktop Entry", "Icon", os.path.join(path, self.filename))
    cf.write(open(os.path.join(path, ".directory"), "w"))

  def removeCover(self, path):
    if not self.enabled:
      return
    
    # check that it is not a file
    if os.path.isfile(path):
      return

    try:
      os.unlink(os.path.join(path, self.filename))
    except OSError:
      pass

    # .directory-file entry
    cf=MyParser()
    try:
      cf.read(os.path.join(path, ".directory"))
    except:
      pass
      
    try:
      cf.remove_option("Desktop Entry", "Icon")
      cf.write(open(os.path.join(path, ".directory"), "w"))
    except:
      pass

  def hasCover(self, path):
    if self.enabled and not os.path.isfile(path):
      return os.path.isfile(os.path.join(path,self.filename))

# -*- coding: iso-8859-1 -*-

import ConfigParser
import os

def getConfigPath(appname):
  """Returns a path that holds the configuration for the application."""
  if appname:
    if os.name=="posix":
      path = os.path.expanduser("~/." + appname)
      try:
        os.mkdir(path)
      except:
        pass
      return path
    elif os.name=="nt":
      try:
        path = os.path.join(os.environ["APPDATA"], appname)
        try:
          os.mkdir(path)
        except:
          pass
        return path
      except:
        pass
  return "."

def configureObject(object, config, modName = None):
  """Configure the given module with values from 'config'"""
  modName = modName or object.__module__
  mod = __import__(modName)
  object.__configuration__ = cfg = mod.defaultConfig.copy()

  # load configuration
  try:
    for (key, value) in config.items(modName):
      cfg[key] = value
  except:
    pass

  for (key, desc) in mod.configDesc.items():
    # fix the types
    try:
      if desc[0] == "boolean":
        if cfg[key] == 1 or config.getboolean(modName, key):
          cfg[key] = True
        else:
          cfg[key] = False
      elif desc[0] == "integer":
        cfg[key] = int(cfg[key])
      elif desc[0] == "stringlist":
        if type(cfg[key]) != type([]):
          cfg[key] = cfg[key].split(";")
    except:
      pass

  object.configure(cfg)

def readObjectConfiguration(object, config):
  for (key, value) in object.__configuration__.items():
    if not config.has_section(object.__module__):
      config.add_section(object.__module__)
    if type(value) == type([]):
      config.set(object.__module__, key, ";".join(value))
    else:
      config.set(object.__module__, key, value)
  


#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

"""
Routines for automatically retrieving album cover images from various sources.

Copyright (C) 2003 Sami Kyöstilä <skyostil@kempele.fi>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
at your option) any later version.
"""

from __future__ import generators

__module__ = "albumart"

import os
import tempfile
import traceback
import sys

class Module:
  """Base class for a module that provides additional functionality."""
  def configure(self, config):
    """Configure the module with the given dictionary of settings."""
    pass

class Source(Module):
  """A virtual base class that defines an album cover source."""
  def findAlbum(self, name):
    """Return a list of matches for the given search string."""
    pass
  def getCover(self, name):
    """Download an album cover image for the given list of matches.
Returns a list of file names."""
    pass

class Target(Module):
  """A virtual base class that defines an album cover target."""
  def getCover(self, path):
    """Returns a cover image for the given path or None if one isn't found."""
    pass
  def setCover(self, path, cover):
    """Assigns a cover image to the given path. Note that the path may also point to a file."""
    pass
  def removeCover(path):
    """Removes the album image for the given path. Note that the path may also point to a file."""
    pass
  def hasCover(self, path):
    """Returns 1 if the given path has an associated cover image and 0 otherwise."""
    return 0

class Recognizer(Module):
  """A virtual base class for album recognizers. Recognizers extract album and artist
     information from paths and files."""
  def guessArtistAndAlbum(self, path):
    """Returns an (artist, album) tuple for the given path."""
    pass

class Cover(object):
  """A cover image"""
  def __init__(self, path, linkUrl = None, linkText = None):
    self.path = path
    self.linkUrl = linkUrl
    self.linkText = linkText

# the sources to use
sources = []

# the targets to use
targets = []

# the recognizers to use
recognizers = []

def addSource(source):
  global sources
  sources.append(source)

def removeSource(source):
  global sources
  sources.remove(source)

def addTarget(target):
  global targets
  targets.append(target)

def removeTarget(target):
  global targets
  targets.remove(target)

def addRecognizer(recognizer):
  global recognizers
  recognizers.append(recognizer)

def removeRecognizer(recognizer):
  global recognizers
  recognizers.remove(recognizer)

def getAvailableCovers(artist, album, requireExactMatch = False):
  """
  Downloads a set of cover images for the given artist/album pair and
  returns an iterator for the list of file names.

  You might use this function as follows:

    for coverfile in albumart.getAvailableCovers(artist,album):
      [do something with the image]
  """

  try:
    for s in sources:
      results = []
      
      try:
        results += s.findAlbum("%s" % (artist), "%s" % (album))
      except TypeError:
        if requireExactMatch:
          continue

        try:
          results+=s.findAlbum("", "%s" % (album))
        except TypeError:
          try:
            results+=s.findAlbum("%s" % (artist), "")
          except TypeError:
            pass

      for a in results:
        c = s.getCover(a)
        if c:
          assert isinstance(c, Cover)
          yield c
  except GeneratorExit:
    pass
  except Exception, x:
    traceback.print_exc(file = sys.stderr)
    raise

def guessArtistAndAlbum(path):
  """Given a path/file, try to extract the artist and album.
     Returns an (artist, album) tuple."""
  
  artist = None
  album = None
  
  for r in recognizers:
    try:
      (artist, album) = r.guessArtistAndAlbum(path)
      if artist and album:
        break
    except Exception, x:
      traceback.print_exc(file = sys.stderr)
     
  return (artist, album)

def synchronizeCovers(path):
  """Makes sure all the cover image targets for the given path
     have the same image."""

  image = None
  imageSource = None

  # find an image for the path
  for t in targets:
    image = t.getCover(path)
    if image:
      imageSource = t
      break

  if image:
    for t in targets:
      # don't set the same image again if we got it from this target
      if t == imageSource:
        continue
      try:
        t.setCover(path, image)
      except:
        pass

def hasCover(path):
  """Returns true if the specified path has an album image set."""
  for t in targets:
    try:
      if t.hasCover(path):
        return True
    except:
      pass
  return False

def setCover(path,cover):
  """Sets the specified album cover for the given path."""
  for t in targets:
    t.setCover(path, cover)

def getCover(path):
  """Returns an album cover for the given path, or None if no image is found."""
  for t in targets:
    c = t.getCover(path)
    if c: return c
  return None

def removeCover(path):
  """Removes the album image for the given path."""
  for t in targets:
    t.removeCover(path)

#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

"""
Routines for automatically retrieving album cover images from various sources.

Copyright (C) 2003 Sami Ky�stil� <skyostil@kempele.fi>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
at your option) any later version.
"""

__module__ = "albumart"

from __future__ import generators

import os

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
		"""Download an album cover image for the given list of matches. Returns a list of file names."""
		pass
#	def setEnabled(self, enabled):
#		"""Enables or disables this module."""
#		pass

class Target(Module):
	"""A virtual base class that defines an album cover target."""
	def getCover(self, path):
		"""Returns a cover image for the given path or None if one isn't found."""
		pass
	def setCover(self, path, cover):
		"""Assigns a cover image to the given path."""
		pass
	def hasCover(self, path):
		"""Returns 1 if the given path has an associated cover image and 0 otherwise."""
		return 0
#	def setEnabled(self, enabled):
#		"""Enables or disables this module."""
#		pass

# the sources to use
#from albumart_source_amazon import Amazon
#sources = [Amazon]

# the targets to use
#from albumart_target_freedesktop import Freedesktop
#from albumart_target_windows import Windows
#targets = [Freedesktop, Windows]

sources = []
targets = []

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

def getAvailableCovers(artist,album):
	"""
	Downloads a set of cover images for the given artist/album pair and returns an iterator for the list of file names.

	You might use this function as follows:

		for coverfile in albumart.getAvailableCovers(artist,album):
			[do something with the image]
	"""

	covers = []
	for s in sources:
		results = []

		try:
			results+=s.findAlbum("%s %s" % (artist,album))
		except TypeError:
			try:
				results+=s.findAlbum("%s" % (album))
			except TypeError:
				try:
					results+=s.findAlbum("%s" % (artist))
				except TypeError:
					pass

		for a in results:
			yield s.getCover(a)

def guessArtistAndAlbum(path):
	"""Given a path, try to extract the artist and album. Works in cases such as:

		artist/album
		artist - album/
		...

	"""
	try:
		p = os.path.split(path)
		artist = p[0]
		album = p[-1]
	except:
		artist = None
		album = path
	if album.find("- ")>0:
		(artist,album) = album.split("-",1)

	artist = artist.strip()
	album = album.strip()

	if not len(artist): artist=None
	if not len(album): album=None

	if not artist and (album and len(album)):
		return (album,None)

	return (artist,album)

def hasCover(path):
	"""Returns true if the specified path has an album image set."""
#	return os.path.isfile(os.path.join(path,"folder.jpg")) or os.path.isfile(os.path.join(path,".folder.png"))
	for t in targets:
		if t.hasCover(path):
			return 1
	return 0

def setCover(path,cover):
	"""Sets the specified album image for the given path."""
	for t in targets:
		t.setCover(path, cover)

	# windows xp
#	coverfile = os.path.join(path,"folder.jpg")

	# freedesktop.org .desktop-file standard
#	coverfile_png = os.path.join(path,".folder.png")

	# We used to just copy over the image...
#	try:
#		shutil.copy(cover,coverfile)
#	except OSError, n:
#		# ignore chmod-errors
#		if not n.errno==1: raise

	# but now we make sure it is in the proper format.
#	i = Image.open(cover)
#	i.save(coverfile, "JPG")
#	i.save(coverfile_png, "PNG")

	# we used to do this with ImageMagick:
#	os.spawnl(os.P_WAIT, "/usr/bin/convert", "/usr/bin/convert", coverfile, coverfile_png)
#	os.system("convert '%s' '%s'" % (coverfile, coverfile_png))


def getCover(path):
	"""Returns an album cover image file for the given path, or None if no image is found."""
	for t in targets:
		c = t.getCover(path)
		if c: return c
	return None
#	if os.path.isfile(os.path.join(path,"folder.jpg")):
#		return os.path.join(path,"folder.jpg")
#	if os.path.isfile(os.path.join(path,".folder.png")):
#		return os.path.join(path,".folder.png")
#	return None


#def process(root, dirname, names):
#	if dirname == root: return
#	if not root[:-1] == os.sep: root+=os.sep
#	dirname=dirname.replace(root,"")
#	(artist,album)=guessArtistAndAlbum(dirname.replace(root,""))
#	print artist, album

#def walk(path):
#	os.path.walk(path, process, path)

#if __name__=="__main__":
#	walk(".")

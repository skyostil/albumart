#!/usr/bin/python

"""
Routines for automatically retrieving album cover images from various sources.

Copyright (C) 2003 Sami Kyöstilä <skyostil@kempele.fi>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
at your option) any later version.
"""

import urllib
import tempfile
import os
import amazon
import shutil
import ConfigParser

class Source:
	"""A virtual base class that defines an album cover source."""
	def findAlbum(self, name):
		"""Return a list of matches for the given search string."""
		pass
	def getCover(self, name):
		"""Download an album cover image for the given list of matches. Returns a list of file names."""
		pass

class Amazon(Source):
	"""Amazon.com album cover source."""
	def findAlbum(self,name):
		try:
			return amazon.searchByKeyword(name,type="lite",product_line="music")
		except amazon.AmazonError:
			pass

	def getCover(self,album):
		try:
			i = urllib.urlopen(album.ImageUrlLarge)
			output = tempfile.mktemp(".jpg")
			o = open(output, "wb")
			o.write(i.read())
			o.close()
			print output
			return output
		except:
			return None

# the used sources
sources = [Amazon]

def getAvailableCovers(artist,album):
	"""Downloads a list of cover images for the given artist/album pair and returns the list of file names."""
	covers = []
	for src in sources:
		s = src()

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
			covers.append(s.getCover(a))

	return covers

def guessArtistAndAlbum(path):
	"""Given a path, try to extract the artist and album. Works on cases such as:

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

	if not artist and len(album):
		return (album,None)

	return (artist,album)

def hasCover(path):
	"""Returns true if the specified path has an album image set."""
	return os.path.isfile(os.path.join(path,"folder.jpg")) and os.path.isfile(os.path.join(path,".folder.png"))

# A wrapper around a file to work around the fact that
# ConfigParser writes keys in lowercase.
class MyWriter(file):
	def write(self,data):
		if data.startswith("icon ="):
			data = "Icon =" + data[6:]
		file.write(self,data)

def setCover(path,cover):
	"""Sets the specified album image for the given path."""

	# windows xp
	coverfile = os.path.join(path,"folder.jpg")
	# freedesktop.org .desktop-file standard
	coverfile_png = os.path.join(path,".folder.png")

	try:
		shutil.copy(cover,coverfile)
	except OSError, n:
		# ignore chmod-errors
		if not n.errno==1: raise

	os.spawnl(os.P_WAIT, "/usr/bin/convert", "/usr/bin/convert", coverfile, coverfile_png)
	#os.system("convert '%s' '%s'" % (coverfile, coverfile_png))

	# .directory-file entry
	cf=ConfigParser.ConfigParser()
	try:
		cf.read(os.path.join(path,".directory"))
	except:
		pass
	if not cf.has_section("Desktop Entry"):
		cf.add_section("Desktop Entry")
	cf.set("Desktop Entry", "Icon", coverfile_png)
	w=MyWriter(os.path.join(path,".directory"),"w")
	cf.write(w)

def process(root, dirname, names):
	if dirname == root: return
	if not root[:-1] == os.sep: root+=os.sep
	dirname=dirname.replace(root,"")
	(artist,album)=guessArtistAndAlbum(dirname.replace(root,""))

	print artist, album

def walk(path):
	os.path.walk(path, process, path)

if __name__=="__main__":
	walk(".")

#!/usr/bin/python

"""
QT-frontend for the album image downloader.

Copyright (C) 2003 Sami Kyöstilä <skyostil@kempele.fi>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
at your option) any later version.
"""

import os
import sys
import albumart
import urllib
import tempfile
import Image
from qt import *

# see if we're using an old Qt version
if qVersion().split(".")[0]=="2":
	from albumartdialog_qt230 import AlbumArtDialog
else:
	from albumartdialog import AlbumArtDialog

__program__ = "Album Cover Art Downloader"
__author__ = "Sami Kyöstilä <skyostil@kempele.fi>"
__version__ = "1.1"
__copyright__ = "Copyright (c) 2003 Sami Kyöstilä"
__license__ = "GPL"

class AlbumArt(AlbumArtDialog):
	def __init__(self,parent = None,name = None,fl = 0):
		AlbumArtDialog.__init__(self,parent,name,fl)
		self.coverPixmap = QPixmap("cover.png")
		self.noCoverPixmap = QPixmap("nocover.png")

	def fileExit(self):
		# delete the downloaded covers
		try:
			for f in self.covers:
				os.unlink(f)
		except:
			pass

		sys.exit(0)

	def process(self, root, dirname, names):
		path = dirname
		if dirname == root: return

		# ugly portability hack
		if "\\" in root:
			if not root[-1] == "\\" : root+="\\"
		else:
			if not root[-1] == "/": root+="/"
			
		dirname=dirname.replace(root,"")

		(artist,album)=albumart.guessArtistAndAlbum(dirname)

		item = QListViewItem(self.dirlist, dirname, artist, album)
		if albumart.hasCover(path):
			item.setPixmap(0,self.coverPixmap)
		else:
			item.setPixmap(0,self.noCoverPixmap)

	def walk(self,path):
		self.dir = path
		self.dirlist.clear()
		os.path.walk(path, self.process, path)
		self.dirlist.setEnabled(1)

	def helpAbout(self):
		QMessageBox.information(self, __program__, """%s version %s by %s.
Amazon web api wrapper by Mark Pilgrim (f8dy@diveintomark.org).""" % (__program__,__version__,__author__))

	def fileOpen(self):
		dir=str(QFileDialog.getExistingDirectory("",self,"Choose a directory that contains one or more albums","Choose a directory", 1))
		if dir and len(dir):
			self.walk(dir)

	def dirlist_selectionChanged(self,a0):
		self.selectedAlbum = a0
		self.coverview.clear()
		self.artistEdit.setText(a0.text(1))
		self.albumEdit.setText(a0.text(2))
		self.pushDownload.setEnabled(1)
		self.pushSet.setEnabled(0)
		self.artistEdit.setEnabled(1)
		self.albumEdit.setEnabled(1)
		self.coverview.setEnabled(1)
		self.coverfiles = {}
		self.covers = []

	def addCoverToList(self,coverfile):
		# if we're running on Qt 2, convert the image to a png.
		if qVersion().split(".")[0]=='2':
			newcoverfile = coverfile + ".png"
			i = Image.open(coverfile)
			i.save(newcoverfile, "PNG")
			del i
			os.unlink(coverfile)
			coverfile = newcoverfile
			
		image = QImage(coverfile)
		
		if not image.isNull() and image.width()>1 and image.height()>1:
			# if we're running on Qt 2, do the scaling a bit differently
			if qVersion().split(".")[0]=='2':
				image = image.smoothScale(256,256 * float(image.height())/float(image.width()))
				pixmap = QPixmap()
				pixmap.convertFromImage(image)
				item = QIconViewItem(self.coverview, None, pixmap)
			else:
				image = image.smoothScale(256,256,QImage.ScaleMin)
				item = QIconViewItem(self.coverview, None, QPixmap(image))
				
			self.coverfiles[item] = coverfile
			return 1
		return 0

	def pushDownload_clicked(self):
		# delete the previously downloaded covers
		try:
			for f in self.covers:
				os.unlink(f)
		except:
			pass

		self.coverview.clear()
		try:
			self.covers = albumart.getAvailableCovers(self.artistEdit.text(), self.albumEdit.text())
		except Exception,x:
			QMessageBox.critical(self, __program__,"The following error occured while downloading cover images:\n%s"%str(x))
			self.covers = []
		self.pushSet.setEnabled(0)
		self.coverfiles = {}

		if len(self.covers):
			for c in self.covers:
				self.addCoverToList(c)
		else:
			QMessageBox.information(self, __program__,"Sorry, no cover images were found. Try simpler keywords.\nHowever, if you already have a cover image you'd like to use,\ngo ahead drop it on the cover image list.")

		self.statusBar().message("%d covers found." % len(self.coverfiles.keys()), 5000);

	def coverview_selectionChanged(self,a0):
		self.pushSet.setEnabled(1)
		self.selectedCover=a0

	def pushSet_clicked(self):
		path = os.path.join(self.dir,str(self.selectedAlbum.text(0)))
		cover = self.coverfiles[self.selectedCover]

		try:
			print path, cover
			albumart.setCover(path,cover)
			self.pushSet.setEnabled(0)
			self.selectedAlbum.setPixmap(0,self.coverPixmap)
		except Exception,x:
			QMessageBox.critical(self, __program__,"The following error occured while setting the cover image:\n%s"%str(x))

	def coverview_dropped(self,a0,a1):
		if not self.selectedAlbum:
			return
		
		text = QString()
		if QTextDrag.decode(a0, text):
			try:
				text=str(text)
				text=urllib.unquote(text)
					
				f=urllib.urlopen(text)
				fn=tempfile.mktemp()
				o=open(fn,"wb")
				o.write(f.read())
				o.close()
				self.addCoverToList(fn)
				self.covers.append(fn)
			except Exception,x:
				QMessageBox.critical(self, __program__,"The following error occured while adding the cover image:\n%s"%str(x))
				raise

if __name__=="__main__":
	app = QApplication(sys.argv)
	mainwin = AlbumArt()
	app.setMainWidget(mainwin)

	if "--help" in sys.argv:
		print """Usage:
%s	[directory]""" % sys.argv[0]
		sys.exit(1)

	try:
		mainwin.walk(sys.argv[1])
	except:
		pass

	mainwin.show()
	app.exec_loop()

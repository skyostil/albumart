# -*- coding: iso-8859-1 -*-
#
# QT-frontend for the album image downloader.
# 
# Copyright (C) 2003, 2004 Sami Kyöstilä <skyostil@kempele.fi>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# at your option) any later version.
#

import os
import sys
import traceback
import encodings
import imghdr
import StringIO
import time
import urllib
import tempfile
import Image
import ConfigParser
from qt import *

# local imports
import albumart
import version
import config
from event import *
from process import *

# see if we're using an old Qt version
if qVersion().split(".")[0] == "2":
  from albumartdialog_qt230 import AlbumArtDialog
else:
  from albumartdialog import AlbumArtDialog

class AlbumArtUi(AlbumArtDialog):
  #
  # Constructor. 
  #
  # @param parent Parent widget
  # @param name Widget name
  # @param fl Widget flags
  # @param dataPath Path to data files
  # @param albumPath Path to walk at startup
  #
  def __init__(self, parent = None,
               name = "AlbumArtDialog",
               fl = 0,
               dataPath = ".",
               albumPath = None):
    AlbumArtDialog.__init__(self,parent,name,fl)
    self.config = ConfigParser.ConfigParser()
    self.moduleAttributeMap = {}
    self.iconSize = 64
    self.dir = ""
    self.dataPath = dataPath
    self.lastRepaintTime = 0

    # load the configuration
    try:
      fn = os.path.join(config.getConfigPath("albumart"), "config")
      self.config.read(fn)

      if not self.config.has_section("albumart"):
        self.config.add_section("albumart")

      self.config.set("albumart", "sources",
                      "albumart_source_amazon.Amazon")
      self.config.set("albumart", "targets",
                      "albumart_target_freedesktop.Freedesktop:" +
                      "albumart_target_windows.Windows:" +
                      "albumart_target_id3v2.ID3v2")

      self.settingsMenu = QPopupMenu()
      self.connect(self.settingsMenu,SIGNAL("activated(int)"), self.settingsMenuActivated)
      self.menubar.insertItem(self.tr("&Settings"), self.settingsMenu, -1, 3)

      # global settings
      try:
        self.showCoversAction.setOn(self.config.getboolean("albumart", "showcovers"))
      except Exception,x:
        pass

      try:
        self.iconSize = self.config.getint("albumart", "iconsize")
      except Exception,x:
        pass

      if self.iconSize == 16:
        self.viewIcon_SizeSmallAction.setOn(1)
      elif self.iconSize == 32:
        self.viewIcon_SizeMediumAction.setOn(1);
      elif self.iconSize == 64:
        self.viewIcon_SizeLargeAction.setOn(1);

      for s in self.config.get("albumart", "sources").split(":"):
        mod = self.loadModule(s)
        albumart.addSource(mod)

      self.settingsMenu.insertSeparator()

      for t in self.config.get("albumart", "targets").split(":"):
        mod = self.loadModule(t)
        albumart.addTarget(mod)
    except Exception, x:
      self.reportException(self.tr("Loading settings"), x)

    self.loadIcons()
    self.show()

    # restore the previous directory
    try:
      if albumPath:
        path = albumPath
      else:
        path = self.config.get("albumart", "lastDirectory")
      self.walk(path)
    except Exception, x:
      self.reportException(self.tr("Reading the previous album directory"), x)

  def scaleIconPixmap(self, pixmap):
    if not pixmap.isNull() and pixmap.width()>0 and pixmap.height()>0:
      try:
        pixmap.convertFromImage(pixmap.convertToImage().scale(self.iconSize,self.iconSize))
      except AttributeError:
        # for older Qt 2.x
        pixmap.convertFromImage(pixmap.convertToImage().smoothScale(self.iconSize,self.iconSize))
    return pixmap
  
  #
  # @returns a full path to the given file in the data directory
  #  
  def getResourcePath(self, fileName):
    return os.path.join(self.dataPath, fileName)

  #
  # Load icons for various ui elements.
  #
  def loadIcons(self):
    self.coverPixmap = QPixmap(self.getResourcePath("cover.png"))
    self.noCoverPixmap = QPixmap(self.getResourcePath("nocover.png"))

    self.coverPixmap = self.scaleIconPixmap(self.coverPixmap)
    self.noCoverPixmap = self.scaleIconPixmap(self.noCoverPixmap)

    # replace ugly icons with nicer alpha channeled ones
    try:
      self.fileOpenAction.setIconSet(QIconSet(QPixmap(self.getResourcePath("fileopen.png"))))
      self.fileExitAction.setIconSet(QIconSet(QPixmap(self.getResourcePath("exit.png"))))
      self.helpAboutAction.setIconSet(QIconSet(QPixmap(self.getResourcePath("icon.png"))))
      self.reloadAction.setIconSet(QIconSet(QPixmap(self.getResourcePath("reload.png"))))
      self.nextAction.setIconSet(QIconSet(QPixmap(self.getResourcePath("1rightarrow.png"))))
      self.previousAction.setIconSet(QIconSet(QPixmap(self.getResourcePath("1leftarrow.png"))))
      self.pushDownload.setIconSet(QIconSet(QPixmap(self.getResourcePath("download.png"))))
      self.pushSet.setIconSet(QIconSet(QPixmap(self.getResourcePath("filesave.png"))))
    except:
      # if that doesn't work, never mind
      pass

  #
  # Load a module with the given name (id)
  #      
  def loadModule(self, id):
    try:
      (mod, cls) = id.split(".")
      exec("import %s" % (mod))
      exec("cfg = %s.defaultConfig.copy()" % (mod))
      exec("cfgdesc = %s.configDesc" % (mod))
      exec("c = %s.%s()" % (mod,cls))

      # load configuration
      try:
        if sys.version_info[:2] == (2,2):
            for key in self.config.options(mod):
              cfg[key] = self.config.get(mod,key)
        else:
            for (key,value) in self.config.items(mod):
              cfg[key] = value
      except:
        pass

      c.__configuration__ = cfg

      for (key,desc) in cfgdesc.items():
        i = self.settingsMenu.insertItem(desc[1])
        self.moduleAttributeMap[i] = (c,key,desc)

        try:
          if desc[0]=="boolean":
            if cfg[key]==1 or self.config.getboolean(mod,key):
              self.settingsMenu.setItemChecked(i, 1)
              cfg[key] = 1
            else:
              cfg[key] = 0
        except:
          pass

      c.configure(cfg)
      return c
    except Exception, x:
      self.reportException(self.getQString(self.tr("Loading module '%s'")) % (id), x)
      
  #
  # Reports the given exception to the user.
  #
  # @param task Description of task during which the exception was raised
  # @param exception The exception that was raised
  # @param silent Pass True if a dialog box shouldn't be shown.
  #
  def reportException(self, task, exception, silent = False):
    xcpt = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    msg = self.getQString(self.tr(
            "%(task)s was interrupted by the following exception:\n<b>%(xcpt)s</b>\n")) % \
            {"task" : task, "xcpt": xcpt}
    sys.stderr.write(msg)
    if not silent:
      QMessageBox.critical(self, version.__program__, msg)

  def showCoversAction_toggled(self, enabled):
    self.config.set("albumart", "showcovers", enabled)
    self.reloadAction_activated()
  
  #
  # Sets the album cover icons to the given pixel size.
  #
  def setIconSize(self, pixels):
    self.iconSize = pixels
    self.config.set("albumart", "iconsize", self.iconSize)
    self.loadIcons()
    self.reloadAction_activated()

  def iconSizeSmallAction_toggled(self, enabled):
    if enabled:
      self.setIconSize(16)

  def iconSizeMediumAction_toggled(self, enabled):
    if enabled:
      self.setIconSize(32)

  def iconSizeLargeAction_toggled(self, enabled):
    if enabled:
      self.setIconSize(64)

  def settingsMenuActivated(self, id):
    enabled = not self.settingsMenu.isItemChecked(id)

    # display a dialog for editing the given setting item
    if self.moduleAttributeMap.has_key(id):
      (mod,key,desc) = self.moduleAttributeMap[id]

      if desc[0] == "boolean":
        self.settingsMenu.setItemChecked(id, enabled)
        mod.__configuration__[key] = enabled
        mod.configure(mod.__configuration__)
      elif desc[0] == "string":
        (text,status) = QInputDialog.getText(desc[1], desc[2], QLineEdit.Normal, mod.__configuration__[key], self)
        if status:
          mod.__configuration__[key] = unicode(text)
          mod.configure(mod.__configuration__)

  def fileExit(self):
    self.close()

  def closeEvent(self, ce):
    # delete the downloaded covers
    try:
      for f in self.covers:
        os.unlink(f)
    except:
      pass

    # save the configuration
    try:
      for mod in albumart.sources + albumart.targets:
        for (key,value) in mod.__configuration__.items():
          if not self.config.has_section(mod.__module__):
            self.config.add_section(mod.__module__)
          self.config.set(mod.__module__, key, value)

      fn = os.path.join(config.getConfigPath("albumart"), "config")
      self.config.write(open(fn,"w"))
    except Exception, x:
      self.reportException(self.tr("Saving settings"), x)
      
    ce.accept()

  #
  # @returns a QPixmap representing the given path
  #
  def getPixmapForPath(self, path):
    if albumart.hasCover(path):
      filename = albumart.getCover(path)

      if filename:
        # if we're running on Qt 2, convert the image to a png.
        if qVersion().split(".")[0]=='2' and imghdr.what(filename) != "png":
          try:
              i = Image.open(filename)
              s = StringIO.StringIO()
              i.save(s, "PNG")
              pixmap = QPixmap()
              pixmap.loadFromData(s.getvalue())
          except IOError:
              return self.noCoverPixmap
        else:
            pixmap = QPixmap(filename)
            
        #pixmap = self.scaleIconPixmap(pixmap)
        if pixmap.width()>0 and pixmap.height()>0:
          return pixmap
        else:
          return self.noCoverPixmap
      else:
        return self.noCoverPixmap
    return self.noCoverPixmap

  #
  # @returns a QPixmap that can be used as an icon for the given path.
  #
  def getIconForPath(self, path):
    if self.showCoversAction and not self.showCoversAction.isOn():
      if albumart.hasCover(path):
        return self.scaleIconPixmap(self.coverPixmap)
      return self.scaleIconPixmap(self.noCoverPixmap)
    return self.scaleIconPixmap(self.getPixmapForPath(path))

  def process(self, root, dirname, names):
    # repaint often enough
    if time.time() > self.lastRepaintTime + 0.25:
      self.lastRepaintTime = time.time()
      qApp.processEvents()

    path = dirname

    # filter out hidden directories
    for d in dirname.split(os.sep):
      if len(d) and d[0]==".":
        return

    # ugly portability hack
    if len(root):
      if "\\" in root:
        if not root[-1] == "\\" : root+="\\"
      else:
        if not root[-1] == "/": root+="/"

    dirname=dirname.replace(root,"")

    if not len(dirname):
      dirname="."

    (artist,album)=albumart.guessArtistAndAlbum(dirname)

    item = QListViewItem(self.dirlist, dirname, artist, album)
    item.setPixmap(0, self.getIconForPath(path))

  #
  # Walk the given path and fill the album list with all the albums found.
  #
  def walk(self, path):
    self.dir = path

    self.pushSet.setEnabled(0)      
    self.fileOpenAction.setEnabled(0)
    self.pushDownload.setEnabled(0)
    self.artistEdit.setEnabled(0)
    self.albumEdit.setEnabled(0)
    self.artistEdit.clear()
    self.removeAction.setEnabled(0)
    self.removeAllAction.setEnabled(1)
    self.albumEdit.clear()
    self.coverview.setEnabled(0)
    self.coverview.clear()
    self.albumIcon.setPixmap(QPixmap())
    self.albumIcon.setEnabled(0)
    self.autoDownloadAction.setEnabled(0)
    self.synchronizeAction.setEnabled(0)
    self.dirlist.setEnabled(1)
    self.dirlist.clear()

    self.statusBar().message(self.tr("Reading directory..."))
    self.setCursor(Qt.waitCursor)
    os.path.walk(path, self.process, path)
    self.statusBar().message(self.tr("Ready"), 5000)
    self.setCursor(Qt.arrowCursor)

    self.pushDownload.setEnabled(0)

    self.reloadAction.setEnabled(1)
    self.nextAction.setEnabled(1)
    self.previousAction.setEnabled(1)
    self.autoDownloadAction.setEnabled(1)
    self.synchronizeAction.setEnabled(1)
    self.fileOpenAction.setEnabled(1)
    
  def helpAbout(self):
    QMessageBox.information(self, version.__program__, self.getQString(self.tr("""\
%(app)s version %(version)s by %(author)s.
http://kempele.fi/~skyostil/projects/albumart

Amazon web api wrapper by Mark Pilgrim and Michael Josephson (http://www.josephson.org/projects/pyamazon/)
Icons by Everaldo Coelho (http://www.everaldo.com) et al.
PyID3 by Myers Carpenter (http://icepick.info/projects/pyid3/)
""")) % \
    ({
      "app" : version.__program__, 
      "version" : version.__version__, 
      "author" : version.__author__
    }))

  def fileOpen(self):
    d = self.getQString(
     QFileDialog.getExistingDirectory(
       self.dir, self,
       self.tr("Choose a directory that contains one or more albums"),
       self.tr("Choose a directory"),
       1))
    if d and len(d):
      self.config.set("albumart", "lastDirectory", d)
      self.walk(d)

  def reloadAction_activated(self):
    if len(self.dir):
      self.walk(self.dir)

  def removeAction_activated(self):
    if QMessageBox.information(self,
         self.tr("Confirm deletion"),
         self.tr("Are you sure you want to delete the selected cover image?"),
         QMessageBox.Yes + QMessageBox.Default,
         QMessageBox.No + QMessageBox.Escape) == QMessageBox.Yes:
      self.setCursor(Qt.waitCursor)
      self.statusBar().message("Deleting selected cover image...")
      
      path = os.path.join(self.dir,self.getQString(self.selectedAlbum.text(0)))
      try:
        albumart.removeCover(path)
        self.updateIcon()
        self.selectedAlbum.setPixmap(0,self.getIconForPath(path))
      except Exception, x:
        self.reportException(self.tr("Removing the cover"), x)

      self.setCursor(Qt.arrowCursor)
      self.statusBar().message("Ready",5000)

  def removeAllAction_activated(self):
    if QMessageBox.information(self,
         self.tr("Confirm deletion"),
         self.tr("Are you really sure you want to delete <b>all</b> the cover images?"),
         QMessageBox.Yes,
         QMessageBox.No + QMessageBox.Default + QMessageBox.Escape) == QMessageBox.Yes:
      item = self.dirlist.firstChild()
      items = []
  
      self.setCursor(Qt.waitCursor)
      self.statusBar().message(self.tr("Preparing deletion..."))
      while item:
        path = os.path.join(self.dir, self.getQString(item.text(0)))
        items.append(path)
        item = item.itemBelow()
        qApp.processEvents();
  
      self.setCursor(Qt.arrowCursor)
      self.statusBar().message("")
      self.startProcess(DeleteProcess(self, self.dir, items))

  #
  # Focus the next album without a cover
  #
  def nextAction_activated(self):
    item = self.dirlist.selectedItem()

    if not item:
      item = self.dirlist.firstChild()

    while item:
      item = item.itemBelow()
      if not item: break
      path = os.path.join(self.dir, self.getQString(item.text(0)))
      if not albumart.hasCover(path):
        self.dirlist.setSelected(item, 1)
        self.dirlist.ensureItemVisible(item)
        break

  #
  # Focus the previous album without a cover
  #
  def previousAction_activated(self):
    item = self.dirlist.selectedItem()

    if not item:
      item = self.dirlist.lastChild()

    while item:
      item = item.itemAbove()
      if not item: break
      path = os.path.join(self.dir, self.getQString(item.text(0)))
      if not albumart.hasCover(path):
        self.dirlist.setSelected(item, 1)
        self.dirlist.ensureItemVisible(item)
        break

  #
  # Runs the given process instance. @see process.Process
  #
  def startProcess(self, process):
    self.progressDialog = QProgressDialog(self, "progress", 1)
    self.progressDialog.setCaption(process.__doc__)
    self.thread = process

    # looks like trolltech fixed their spelling in Qt 3
    if qVersion().split(".")[0]=="2":
      self.progressDialog.connect(self.progressDialog, SIGNAL("cancelled()"), self.processCanceled)
    else:
      self.progressDialog.connect(self.progressDialog, SIGNAL("canceled()"), self.processCanceled)

    self.progressDialog.show()
    self.thread.start()

  #
  # Cancels the active process
  #
  def processCanceled(self):
    if self.thread:
      self.thread.cancel()

  #
  # Download images automatically for all the albums
  #
  def autoDownloadAction_activated(self):
    item = self.dirlist.firstChild()
    items = []
    recognized = 0
    coversFound = 0
    coversInstalled = 0

    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Preparing automatic download..."))
    while item:
      path = os.path.join(self.dir, self.getQString(item.text(0)))
      if not albumart.hasCover(path):
        items.append(path)
      item = item.itemBelow()
      qApp.processEvents();

    self.setCursor(Qt.arrowCursor)
    self.statusBar().message("")
    self.startProcess(AutoDownloadProcess(self, self.dir, items))

  #
  # Make sure all the albums have same images in all their targets
  # (fd.o, wxp, id3v2, etc.)
  #
  def synchronizeAction_activated(self):
    item = self.dirlist.firstChild()
    items = []

    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Preparing synchronization..."))
    while item:
      path = os.path.join(self.dir, self.getQString(item.text(0)))
      if albumart.hasCover(path):
        items.append(path)
      item = item.itemBelow()
      qApp.processEvents();

    self.setCursor(Qt.arrowCursor)
    self.statusBar().message("")
    self.startProcess(SynchronizeProcess(self, self.dir, items))

  def dirlist_selectionChanged(self, a0):
    # delete downloaded covers
    try:
      for f in self.covers:
        os.unlink(f)
    except:
      pass
  
    self.selectedAlbum = a0
    self.coverview.clear()
    self.artistEdit.setText(a0.text(1))
    self.albumEdit.setText(a0.text(2))
    self.pushDownload.setEnabled(1)
    self.removeAction.setEnabled(1)
    self.pushSet.setEnabled(0)
    self.artistEdit.setEnabled(1)
    self.albumEdit.setEnabled(1)
    self.coverview.setEnabled(1)
    self.coverfiles = {}    # a map of listiview items to cover files
    self.covers = []  # a list of downloaded covers
    self.thread = None
    self.statusBar().message("")
    self.updateIcon()

  #
  # @returns a python string representation of the given QString
  #
  def getQString(self, qstring):
    return unicode(qstring).encode("latin-1", "replace")

  #
  # Update the icon of the currently selected album.
  #
  def updateIcon(self):
    # Try to load the current album cover image and display it as the folder icon.
    try:
      self.albumIcon.setEnabled(0)
      self.albumIcon.setPixmap(QPixmap())
      path = os.path.join(self.dir,self.getQString(self.selectedAlbum.text(0)))

      if albumart.hasCover(path):
        pixmap = self.getPixmapForPath(path)
        image = pixmap.convertToImage()

        if not image.isNull() and image.width()>1 and image.height()>1:
          image = image.smoothScale(60,60)
          pixmap.convertFromImage(image)
          self.albumIcon.setPixmap(pixmap)
          self.albumIcon.setEnabled(1)
    except Exception, x:
      self.reportException(self.tr("Loading the album cover"), x, silent = True)

  def albumIcon_clicked(self):
    # Try to load the current album cover image and display it in as new window
    try:
      path = os.path.join(self.dir,self.getQString(self.selectedAlbum.text(0)))
      pixmap = self.getPixmapForPath(path)
      self.coverPreviewWindow = QLabel(None)
      self.coverPreviewWindow.setPixmap(pixmap)
      self.coverPreviewWindow.setFixedSize(pixmap.width(), pixmap.height())
      self.coverPreviewWindow.setCaption(
        self.getQString(self.tr("Cover image for album %(album)s")) % \
        {"album" : self.getQString(self.selectedAlbum.text(0))})
      self.coverPreviewWindow.show()
    except Exception, x:
      self.reportException(self.tr("Loading the album cover"), x)

  #
  # Adds the given cover to the list of available album covers.
  #
  def addCoverToList(self, coverfile):
    # if we're running on Qt 2, convert the image to a png.
    try:
      if qVersion().split(".")[0]=='2' and imghdr.what(coverfile) != "png":
        i = Image.open(coverfile)
        s = StringIO.StringIO()
        i.save(s, "PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(s.getvalue())
        image = pixmap.convertToImage()
      else:
        image = QImage(coverfile)
    except IOError:
      return 0

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

  def customEvent(self,event):
    try:
      # if the message was sent by an older thread, ignore it.
      if self.thread != event.thread:
        return
    except AttributeError:
      pass
      
    if event.type() == CoverDownloadedEvent.id:
      self.covers.append(event.filename)
      self.addCoverToList(event.filename)
    elif event.type() == TaskFinishedEvent.id:
      self.thread.wait()
      self.thread = None

      if self.progressDialog:
        self.progressDialog.close()

      if event.message:
        QMessageBox.information(self, version.__program__,event.message)

      self.pushDownload.setEnabled(1)
    elif event.type() == ExceptionEvent.id:
      self.reportException(self.tr("Downloading cover images"), event.exception)
    elif event.type() == ProgressEvent.id:
      if self.progressDialog:
        self.progressDialog.setTotalSteps(event.total)
        self.progressDialog.setProgress(event.progress)
    elif event.type() == StatusEvent.id:
      if self.progressDialog:
        self.progressDialog.setLabelText(event.text)
    elif event.type() == ReloadEvent.id:
      self.reloadAction_activated()

    del event

  def pushDownload_clicked(self):
    # delete the previously downloaded covers
    try:
      for f in self.covers:
        os.unlink(f)
    except:
      pass

    self.coverview.clear()
    self.pushSet.setEnabled(0)
    self.pushDownload.setEnabled(0)
    self.coverfiles = {}
    self.covers = []

    # start the downloader thread
    proc = CoverDownloaderProcess(
             self,
             self.getQString(self.artistEdit.text()),
             self.getQString(self.albumEdit.text()))
    self.startProcess(proc)

  def coverview_selectionChanged(self,a0):
    self.pushSet.setEnabled(1)
    self.selectedCover=a0

  def pushSet_clicked(self):
    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Setting cover images..."))

    path = os.path.join(self.dir,self.getQString(self.selectedAlbum.text(0)))
    cover = self.coverfiles[self.selectedCover]

    try:
      albumart.setCover(path,cover)
      self.pushSet.setEnabled(0)
      self.selectedAlbum.setPixmap(0, self.getIconForPath(path))
      self.updateIcon()
    except Exception, x:
      self.reportException(self.tr("Setting the cover image"), x)

    self.setCursor(Qt.arrowCursor)
    self.statusBar().message(self.tr("Ready"), 5000)

  def coverview_dropped(self,a0,a1):
    if not self.selectedAlbum:
      return

    text = QString()
    if QTextDrag.decode(a0, text):
      try:
        text=self.getQString(text)
        text=urllib.unquote(text)

        f=urllib.urlopen(text)
        fn=tempfile.mktemp()

        # write to a temporary file
        o=open(fn,"wb")
        o.write(f.read())
        o.close()

        # convert to JPEG
        img = Image.open(fn)
        img.load()
        img = img.convert("RGB")
        img.save(fn, "JPEG")
        self.addCoverToList(fn)
        self.covers.append(fn)
      except Exception, x:
        self.reportException(self.tr("Adding the cover image"), x)

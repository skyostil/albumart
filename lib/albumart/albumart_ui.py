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
from pixmap import getPixmapForPath
from items import TrackItem, AlbumItem, CoverItem
from event import *
from process import *

# see if we're using an old Qt version
if qVersion().split(".")[0] == "2":
  from albumartdialog_qt230 import AlbumArtDialog
else:
  from albumartdialog import AlbumArtDialog

class AlbumArtUi(AlbumArtDialog):
  """Main window."""
  def __init__(self, parent = None,
               name = "AlbumArtUi",
               fl = 0,
               dataPath = ".",
               albumPath = None):
    """Constructor. 
    
       @param parent Parent widget
       @param name Widget name
       @param fl Widget flags
       @param dataPath Path to data files
       @param albumPath Path to walk at startup"""
    AlbumArtDialog.__init__(self,parent,name,fl)
    self.config = ConfigParser.ConfigParser()
    self.moduleAttributeMap = {}
    self.iconSize = 64
    self.dir = ""
    self.dataPath = dataPath
    self.albums = {}

    # tweak the ui
    self.settingsMenu = QPopupMenu()
    self.connect(self.settingsMenu,SIGNAL("activated(int)"), self.settingsMenuActivated)
    self.menubar.insertItem(self.tr("&Settings"), self.settingsMenu, -1, 3)
    self.dirlist.header().hide()
    
    # enable drag and drop for the album list
    self.dirlist.__class__.dropEvent = self.dirlist_dropEvent
    self.dirlist.__class__.dragEnterEvent = self.dirlist_dragEnterEvent
    self.coverview.__class__.dragObject = self.coverview_dragObject

    self.loadIcons()
    self.show()
    self.loadConfiguration()

    # restore the previous directory
    try:
      if albumPath:
        path = albumPath
      else:
        path = self.config.get("albumart", "lastDirectory")
      self.walk(path)
    except Exception, x:
      self.reportException(self.tr("Reading the previous album directory"), x,
                           silent = False)
    
  def loadConfiguration(self):
    """Load the settings from the configuration file"""
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
      self.config.set("albumart", "recognizers",
                      "albumart_recognizer_id3v2.ID3v2Recognizer:" +
                      "albumart_recognizer_path.PathRecognizer")
      # global settings
      self.settingsMenu.clear()
      try:
        self.hideAlbumsWithCovers.setOn(self.config.getboolean("albumart", "hide_albums_with_covers"))
      except Exception,x:
        self.hideAlbumsWithCovers.setOn(False)

      for s in self.config.get("albumart", "sources").split(":"):
        mod = self.loadModule(s)
        albumart.addSource(mod)

      self.settingsMenu.insertSeparator()

      for t in self.config.get("albumart", "targets").split(":"):
        mod = self.loadModule(t)
        albumart.addTarget(mod)
        
      for t in self.config.get("albumart", "recognizers").split(":"):
        mod = self.loadModule(t)
        albumart.addRecognizer(mod)
        
    except Exception, x:
      self.reportException(self.tr("Loading settings"), x)

  def scaleIconPixmap(self, pixmap):
    """@returns the given pixmap scaled to icon size"""
    return self.scalePixmap(pixmap, self.iconSize)

  def scalePixmap(self, pixmap, size):
    """@returns the given pixmap scaled to a new size
       @param size New pixel size."""
    if not pixmap.isNull() and pixmap.width() > 0 and pixmap.height() > 0:
      try:
        pixmap.convertFromImage(pixmap.convertToImage().scale(size, size))
      except AttributeError:
        # for older Qt 2.x
        pixmap.convertFromImage(pixmap.convertToImage().smoothScale(size, size))
    return pixmap
      
  def getResourcePath(self, fileName):
    """@returns a full path to the given file in the data directory"""
    return os.path.join(self.dataPath, fileName)

  def loadIcons(self):
    """Load icons for various ui elements."""
    self.coverPixmap = QPixmap(self.getResourcePath("cover.png"))
    self.noCoverPixmap = QPixmap(self.getResourcePath("nocover.png"))

    self.coverPixmap = self.scaleIconPixmap(self.coverPixmap)
    self.noCoverPixmap = self.scaleIconPixmap(self.noCoverPixmap)
      
  def loadModule(self, id):
    """Load a module with the given name (id)"""
    try:
      (mod, cls) = id.split(".")
      module = __import__(mod)
      cfg = module.defaultConfig.copy()
      cfgdesc = module.configDesc
      c = module.__dict__[cls]()

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

        # fix the types
        try:
          if desc[0] == "boolean":
            if cfg[key] == 1 or self.config.getboolean(mod,key):
              self.settingsMenu.setItemChecked(i, 1)
              cfg[key] = True
            else:
              cfg[key] = False
        except:
          pass

      c.configure(cfg)
      return c
    except Exception, x:
      self.reportException(self.tr("Loading module '%s'") % (id), x)
      
  def reportException(self, task, exception, silent = False, description = None):
    """Reports the given exception to the user.
  
      @param task Description of task during which the exception was raised
      @param exception The exception that was raised
      @param silent Pass True if a dialog box shouldn't be shown.
      @param description An optional description of the exception.
                         If not given, the description is generated from
                         the system stack."""
    if not description:
        description = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    fullmsg = self.tr(
            "%(task)s was interrupted by the following exception:\n%(description)s\n") % \
            {"task" : task, "description": "".join(description)}
    msg = self.tr(
            "%(task)s was interrupted by the following exception:\n%(description)s\n") % \
            {"task" : task, "description": description[-1]}
    sys.stderr.write(fullmsg)
    if not silent:
      if QMessageBox.critical(self, version.__program__, msg,
                              self.tr("OK"),
                              self.tr("More...")) == 1:
        QMessageBox.critical(self, version.__program__, fullmsg)

  def hideAlbumsWithCovers_toggled(self, enabled):
    self.config.set("albumart", "hide_albums_with_covers", enabled)
    self.refreshAlbumList()
  
  def setIconSize(self, pixels):
    """Sets the album cover icons to the given pixel size."""
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
        (text, status) = QInputDialog.getText(desc[1], desc[2], QLineEdit.Normal, mod.__configuration__[key], self)
        if status:
          mod.__configuration__[key] = unicode(text)
          mod.configure(mod.__configuration__)
      elif desc[0] == "stringlist":
        items = QStringList()
        map(lambda i: items.append(i), desc[3])
        selected = 0
        for i in xrange(0, len(desc[3])):
            if mod.__configuration__[key] == desc[3][i]:
                selected = i
                
        (text, status) = QInputDialog.getItem(desc[1], desc[2], items, selected, True)
        if status:
          mod.__configuration__[key] = unicode(text)
          mod.configure(mod.__configuration__)

  def fileExit(self):
    self.close()

  def closeEvent(self, ce):
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

    # destroy the downloaded covers
    self.coverview.clear()
                
    ce.accept()

  def getIconForPath(self, path):
    """@returns a QPixmap that can be used as an icon for the given path."""
    if self.showCoversAction and not self.showCoversAction.isOn():
      if albumart.hasCover(path):
        return self.scaleIconPixmap(self.coverPixmap)
      return self.scaleIconPixmap(self.noCoverPixmap)
    return self.scaleIconPixmap(self.getPixmapForPath(path))

  def walk(self, path):
    """Walk the given path and fill the album list with all the albums found."""
    self.dir = path
    
    # update the widget states
    self.setCursor(Qt.waitCursor)
    self.fileOpenAction.setEnabled(0)
    self.reloadAction.setEnabled(0)
    
    # clear the db
    self.albums = {}
    
    lastRepaintTime = time.time()
    for root, dirs, files in os.walk(path):
      for n in files:
        if os.path.splitext(n)[1].lower() in albumart.mediaExtensions:
          # update status bar often enough
          if time.time() > lastRepaintTime + 0.2:
            self.statusBar().message(self.tr("Reading %s") % n)
            lastRepaintTime = time.time()
            qApp.processEvents()
            
          p = os.path.join(root, n)
          (artist, album) = albumart.guessArtistAndAlbum(p)
          
          # get the album for this track
          if not (artist, album) in self.albums:
            self.albums[(artist, album)] = []
          
          # add the track to the album 
          self.albums[(artist, album)].append(p)

    self.refreshAlbumList()
    self.statusBar().message(self.tr("%d albums found. Ready.") % len(self.albums), 5000)

    self.reloadAction.setEnabled(1)
    self.fileOpenAction.setEnabled(1)
    self.setCursor(Qt.arrowCursor)
  
  def refreshAlbumList(self):
    """Refreshes the album list according to the current search string."""
    self.setCursor(Qt.waitCursor)
    self.dirlist.clear()
    for (artist, album), tracks in self.albums.items():
      if len(tracks) and self.matchesFilter(artist, album, tracks):
        filteredTracks = []
        
        # filter the tracks
        for t in tracks:
          if self.hideAlbumsWithCovers.isOn() and \
             not albumart.hasCover(t) or \
             not self.hideAlbumsWithCovers.isOn():
            filteredTracks.append(t)
            
        # if the album is not empty, add it to the list
        if len(filteredTracks):
          a = AlbumItem(self.dirlist, os.path.dirname(tracks[0]), artist, album)
          for t in filteredTracks:
            a.addTrack(t)
    self.setCursor(Qt.arrowCursor)
          
  def matchesFilter(self, artist, album, tracks):
    """Tests whether the given artist, album or track list matches
       the current search filter."""
    query = self.getQString(self.filterEdit.text()).lower()
    if not len(query):
      return True
    if query in artist.lower():
      return True
    if query in album.lower():
      return True
    for t in tracks:
      if query in t.lower():
        return True
    return False
    
  def helpAbout(self):
    QMessageBox.information(self, version.__program__, self.tr("""\
%(app)s version %(version)s by %(author)s.
http://kempele.fi/~skyostil/projects/albumart

Amazon web api wrapper by Mark Pilgrim and Michael Josephson (http://www.josephson.org/projects/pyamazon/)
Icons by Everaldo Coelho (http://www.everaldo.com) et al.
PyID3 by Myers Carpenter (http://icepick.info/projects/pyid3/)
""") % \
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
      
      for path in self.getSelectedFiles():
        try:
          albumart.removeCover(path)
        except Exception, x:
          self.reportException(self.tr("Removing the cover"), x)

      self.refreshSelectedFiles()
      self.setCursor(Qt.arrowCursor)
      self.statusBar().message("Ready",5000)

  def selectAllAction_activated(self):
    self.dirlist.selectAll(True)

  def startProcess(self, process):
    """Runs the given process instance. @see process.Process"""
    self.progressDialog = QProgressDialog(self, "progress", 1)
    self.progressDialog.setCaption(process.__doc__)
    self.thread = process

    # looks like trolltech fixed their spelling in Qt 3
    if qVersion().split(".")[0] == "2":
      self.progressDialog.connect(self.progressDialog, SIGNAL("cancelled()"), self.processCanceled)
    else:
      self.progressDialog.connect(self.progressDialog, SIGNAL("canceled()"), self.processCanceled)

    self.progressDialog.show()
    self.thread.start()

  def processCanceled(self):
    """Cancels the active process"""
    if self.thread:
      self.thread.cancel()
      
  def queryEdited(self):
    """Either the album or artists edit boxes were modified"""
    self.pushDownload.setEnabled(
      not self.albumEdit.text().isEmpty() or \
      not self.artistEdit.text().isEmpty())

  def autoDownloadAction_activated(self):
    """Download images automatically for all the albums"""
    item = self.dirlist.firstChild()

    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Preparing automatic download..."))
    items = [file for file in self.getSelectedFiles() if not albumart.hasCover(file)]
    self.setCursor(Qt.arrowCursor)
    self.statusBar().message("")
    self.startProcess(AutoDownloadProcess(self, self.dir, items))

  def synchronizeAction_activated(self):
    """Make sure all the albums have same images in all their targets
       (fd.o, wxp, id3v2, etc.)"""
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

  def dirlist_selectionChanged(self):
    flag = len(self.getSelectedFiles()) > 0
    self.autoDownloadAction.setEnabled(flag)
    self.removeAction.setEnabled(flag)
    
  def dirlist_currentChanged(self, a0):
    self.artistEdit.setText(a0.getArtistName())
    self.albumEdit.setText(a0.getAlbumName())
    self.thread = None

  def dirlist_contextMenuRequested(self, item, point, column):
    if item:
      menu = QPopupMenu()
      self.autoDownloadAction.addTo(menu)
      self.removeAction.addTo(menu)
      self.viewCoverAction.addTo(menu)
      c = albumart.hasCover(item.getPath())
      self.removeAction.setEnabled(c)
      self.viewCoverAction.setEnabled(c)
      menu.exec_loop(point)
    
  def getQString(self, qstring):
    """@returns a python string representation of the given QString"""
    return unicode(qstring).encode("latin-1", "replace")

  def getSelectedFiles(self):
    """@returns a list of selected media files to process"""
    albumItem = self.dirlist.firstChild()
    files = []
    
    while albumItem:
      if albumItem.isSelected():
        files.append(albumItem.getPath())
      trackItem = albumItem.firstChild()
      while trackItem:
        if trackItem.isSelected() or albumItem.isSelected():
          files.append(trackItem.getPath())
        trackItem = trackItem.nextSibling()
      albumItem = albumItem.nextSibling()
    return files

  def getCurrentFiles(self):
    """@returns a list of current (i.e. focused) media files to process"""
    item = self.dirlist.currentItem()
    files = [item.getPath()]
    
    if isinstance(item, AlbumItem):
      trackItem = item.firstChild()
      while trackItem:
        files.append(trackItem.getPath())
        trackItem = trackItem.nextSibling()
    return files
    
  def refreshSelectedFiles(self):
    """Reloads icons for the selected files"""
    albumItem = self.dirlist.firstChild()
    
    while albumItem:
      if albumItem.isSelected():
        albumItem.refresh()
      trackItem = albumItem.firstChild()
      while trackItem:
        if trackItem.isSelected() or albumItem.isSelected():
          trackItem.refresh()
        trackItem = trackItem.nextSibling()
      albumItem = albumItem.nextSibling()

  def refreshCurrentFiles(self):
    """Reloads icons for the current (i.e. focused) files"""
    item = self.dirlist.currentItem()
    item.refresh()
    
    if isinstance(item, AlbumItem):
      trackItem = item.firstChild()
      while trackItem:
        trackItem.refresh()
        trackItem = trackItem.nextSibling()
          
  def addCoverToList(self, coverfile):
    """Adds the given cover to the list of available album covers."""
    # if we're running on Qt 2, convert the image to a png.
    try:
      if qVersion().split(".")[0] == '2' and imghdr.what(coverfile) != "png":
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

    if not image.isNull() and image.width() > 1 and image.height() > 1:
      # if we're running on Qt 2, do the scaling a bit differently
      if qVersion().split(".")[0] == '2':
        image = image.smoothScale(256, 256 * float(image.height()) / float(image.width()))
        pixmap = QPixmap()
        pixmap.convertFromImage(image)
        item = CoverItem(self.coverview, pixmap, coverfile)
      else:
        image = image.smoothScale(256, 256, QImage.ScaleMin)
        item = CoverItem(self.coverview, QPixmap(image), coverfile)

      return 1
    return 0

  def customEvent(self, event):
    """Handle events from processes"""
    # if the message was sent by an older thread, ignore it.
    if self.__dict__.has_key("thread"):
      if self.thread != event.thread:
        return
      
    if event.type() == CoverDownloadedEvent.id:
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
      self.reportException(self.tr("Downloading cover images"),
                           event.exception,
                           description = event.description)
    elif event.type() == ProgressEvent.id:
      if self.progressDialog:
        self.progressDialog.setTotalSteps(event.total)
        self.progressDialog.setProgress(event.progress)
    elif event.type() == StatusEvent.id:
      if self.progressDialog:
        self.progressDialog.setLabelText(event.text)
    elif event.type() == ReloadEvent.id:
      self.refreshSelectedFiles()

    del event

  def pushDownload_clicked(self):
    self.coverview.clear()
    self.pushSet.setEnabled(0)
    self.pushDownload.setEnabled(0)
    
    # start the downloader thread
    proc = CoverDownloaderProcess(
             self,
             self.getQString(self.artistEdit.text()),
             self.getQString(self.albumEdit.text()))
    self.startProcess(proc)

  def coverview_selectionChanged(self,a0):
    self.pushSet.setEnabled(1)
    self.selectedCover = a0

  def coverview_dragObject(self):
    if self.coverview.currentItem():
      d = QTextDrag(self.coverview.currentItem().getPath(), self.coverview)
      d.setPixmap(self.coverview.currentItem().pixmap())
      return d
        
  def pushSet_clicked(self):
    self.setCover(self.coverview.currentItem().getPath())
    
  def setCover(self, coverPath):
    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Setting cover images..."))

    for path in self.getSelectedFiles():
      try:
        albumart.setCover(path, coverPath)
        self.statusBar().message(self.tr("Writing %s") % os.path.basename(path))
        qApp.processEvents()
      except Exception, x:
        self.reportException(self.tr("Setting the cover image"), x)
        
    self.refreshSelectedFiles()
    self.setCursor(Qt.arrowCursor)
    self.statusBar().message(self.tr("Ready"), 5000)
    
  def setCoverForCurrentFiles(self, coverPath):
    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Setting cover images..."))

    for path in self.getCurrentFiles():
      try:
        albumart.setCover(path, coverPath)
      except Exception, x:
        self.reportException(self.tr("Setting the cover image"), x)
        
    self.refreshCurrentFiles()
    self.setCursor(Qt.arrowCursor)
    self.statusBar().message(self.tr("Ready"), 5000)
    
  def decodeDropEventAsCover(self, event):
    """@returns a file name for the given cover drop event or None or error.
       Remember to clean up the file returned by this function."""
    if QTextDrag.canDecode(event):
      s = QString()
      if QTextDrag.decode(event, s):
        url = urllib.unquote(self.getQString(s))
        f = urllib.urlopen(url)
        fn = tempfile.mktemp()

        # write to a temporary file
        o = open(fn,"wb")
        o.write(f.read())
        o.close()

        # convert to JPEG
        img = Image.open(fn)
        img.load()
        img = img.convert("RGB")
        img.save(fn, "JPEG", quality = 100)
        return fn
  
  def dirlist_dropEvent(self, event):
    # check whether it is a path
    if QTextDrag.canDecode(event):
      s = QString()
      if QTextDrag.decode(event, s):
        url = urllib.unquote(self.getQString(s)).strip()
        if url.startswith("file:"):
          url = url[len("file:"):]
        if os.path.isdir(url):
          self.walk(url)
          return
    
    try:
      fn = self.decodeDropEventAsCover(event)
      if fn:
        event.accept(True)
        self.setCoverForCurrentFiles(fn)
        os.unlink(fn)
    except Exception, x:
      self.reportException(self.tr("Setting the cover image"), x)
  
  def dirlist_dragEnterEvent(self, event):
    if QTextDrag.canDecode(event):
      event.accept()

  def viewCoverImage(self):
    """Try to load the current album cover image and display it in as new window"""
    try:
      pixmap = getPixmapForPath(self.dirlist.currentItem().getPath())
      self.window = QLabel(None)
      self.window.setPixmap(pixmap)
      self.window.setFixedSize(pixmap.width(), pixmap.height())
      self.window.show()
    except Exception, x:
      self.reportException(self.tr("Loading the album cover"), x)
    
  def filterChanged(self):
    if not "filterTimer" in self.__dict__:
      self.filterTimer = QTimer(self)
      self.connect(self.filterTimer, SIGNAL("timeout()"), self.refreshAlbumList)
    self.filterTimer.start(500, True)

  def tr(self, identifier, context = None):
    """Overridden translation method that returns native Python strings"""
    if qVersion().split(".")[0] == "2":
        # tr is static in old Qt
        return self.getQString(QObject.tr(identifier, context))
    return self.getQString(QObject.tr(self, identifier, context))

  def coverview_dropped(self, event, a1):
    try:
      fn = self.decodeDropEventAsCover(event)
      if fn:
        self.addCoverToList(fn)
    except Exception, x:
      self.reportException(self.tr("Adding the cover image"), x)

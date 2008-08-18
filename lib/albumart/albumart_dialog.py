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

"""Album Cover Art Downloader"""

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
import cPickle as pickle
import codecs
from qt import *

# local imports
import albumart
import version
import config
from pixmap import getPixmapForPath, resizePixmap
from items import TrackItem, AlbumItem, CoverItem, FolderItem, FileItem
from event import *
from process import *
from albumart_dialog_base import AlbumArtDialogBase
from albumart_configuration_dialog import ConfigurationDialog
from albumart_about_dialog import AboutDialog
from albumart_exception_dialog import ExceptionDialog
from albumart_progress_widget import ProgressWidget

defaultConfig = {
  "last_directory":  "",
  "media_extensions": ["mp3", "ogg", "wma", "flac", "wav", "mpa", "mp2", "m4a", "mp4", "m4p", "aac",
                       "la", "pac", "ape", "ofr", "rka", "shn", "tta", "wv", "mpc", "vqf", "ra",
                       "rm", "swa", "mid", "mod", "nsf", "s3m", "xm", "it", "mt2", "sid"],
  "hide_albums_with_covers": "0",
  "require_exact_match": True,
  "view_mode": "0",
  "sources": ["albumart_source_walmart.Walmart",
              "albumart_source_buy.Buy",
              "albumart_source_yahoo.Yahoo",
              "albumart_source_amazon.Amazon"],
  "targets": ["albumart_target_freedesktop.Freedesktop",
              "albumart_target_windows.Windows",
              "albumart_target_id3v2.ID3v2",
              "albumart_target_generic.Generic"],
  "recognizers": ["albumart_recognizer_id3v2.ID3v2Recognizer",
                  "albumart_recognizer_path.PathRecognizer"]
}

configDesc = {
  "media_extensions": ("stringlist", """<qt>
<p>Media file extensions.</p>
<p>The file types listed here
will be treated as media files.</p>
</qt>"""),
  "sources": ("stringlist",),
  "targets": ("stringlist",),
  "recognizers": ("stringlist",),
  "require_exact_match": ("boolean", "Require an exact match when searching for covers automatically."),
  "hide_albums_with_covers": ("boolean",),
}

class AlbumArtDialog(AlbumArtDialogBase):
  """General"""
  def __init__(self, parent = None,
               name = "AlbumArtDialog",
               fl = 0,
               dataPath = ".",
               albumPath = ""):
    """Constructor.

       @param parent Parent widget
       @param name Widget name
       @param fl Widget flags
       @param dataPath Path to data files
       @param albumPath Path to walk at startup"""
    AlbumArtDialogBase.__init__(self, parent, name, fl)
    self.moduleAttributeMap = {}
    self.dir = ""
    self.dataPath = dataPath
    self.albums = {}
    self.modules = []
    self.cachePath = os.path.join(config.getConfigPath("albumart"), "cache")
    self.currentCoverItems = []
    self.progressWidget = None

    # tweak the ui
    self.dirlist.header().hide()

    # enable drag and drop for the album list
    self.dirlist.__class__.dropEvent = self.dirlist_dropEvent
    self.dirlist.__class__.dragEnterEvent = self.dirlist_dragEnterEvent
    self.coverview.__class__.dragObject = self.coverview_dragObject

    self.coverview.connect(self.coverview, SIGNAL("clicked(QIconViewItem*,const QPoint&)"), self.coverview_itemClicked)
    self.show()

    # load configuration
    self.config = ConfigParser.RawConfigParser()
    self.loadConfiguration()

    if albumPath:
      self.dir = albumPath

    # restore the previous directory
    try:
      if self.dir:
        self.walk(self.dir)
    except Exception, x:
      self.reportException(self.tr("Reading the previous album directory"), x,
                           silent = False)

  def coverview_itemClicked(self, item, pos):
    # For some reason, clicks on the cover text labels are not associated
    # with the item itself
    pos = self.coverview.mapFromGlobal(pos)
    if not item:
      item = self.coverview.findItem(pos)
    if item:
      itemPos = self.coverview.contentsToViewport(item.pos())
      pos = QPoint(pos.x() - itemPos.x(), pos.y() - itemPos.y())
      item.onClicked(pos)

  def configure(self, config):
    # some day we might find the plugins dynamically
    for c in ["sources", "targets", "recognizers"]:
      config[c] = defaultConfig[c]

    self.mediaExtensions = config["media_extensions"]
    self.dir = config["last_directory"]
    self.requireExactMatch = config["require_exact_match"]
    self.hideAlbumsWithCovers.setOn(config["hide_albums_with_covers"] and True or False)
    self.viewAlbumsAction.setOn(config["view_mode"] == "0")
    self.viewFoldersAction.setOn(config["view_mode"] == "1")

    # only load plugins at startup
    if not self.modules:
      for id in config["sources"]:
        albumart.addSource(self.loadModule(id))

      for id in config["targets"]:
        albumart.addTarget(self.loadModule(id))

      for id in config["recognizers"]:
        albumart.addRecognizer(self.loadModule(id))

  def loadConfiguration(self):
    """Load the settings from the configuration file"""
    try:
      fn = os.path.join(config.getConfigPath("albumart"), "config")
      self.config.read(fn)

      if not self.config.has_section("albumart"):
        self.config.add_section("albumart")

      config.configureObject(self, self.config)
    except Exception, x:
      self.reportException(self.tr("Loading settings"), x)


  def loadModule(self, id):
    """Load a module with the given name (id)"""
    try:
      (mod, cls) = id.split(".")
      module = __import__(mod)
      c = module.__dict__[cls]()
      config.configureObject(c, self.config)
      self.modules.append(c)
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
      ExceptionDialog(self, task, description).exec_loop()

  def hideAlbumsWithCovers_toggled(self, enabled):
    self.config.set("albumart", "hide_albums_with_covers", enabled)
    self.refreshAlbumList()

  def fileExit(self):
    self.close()

  def saveConfiguration(self):
    self.__configuration__["view_mode"] = self.viewAlbumsAction.isOn() and "0" or "1"
    self.__configuration__["last_directory"] = self.dir

    try:
      for object in self.modules + [self]:
        config.readObjectConfiguration(object, self.config)
      fn = os.path.join(config.getConfigPath("albumart"), "config")
      for section in self.config.sections():
        for option, value in self.config.items(section):
          self.config.set(section, option, unicode(value).encode(sys.getfilesystemencoding()))
      self.config.write(open(fn, "w"))
    except Exception, x:
      self.reportException(self.tr("Saving settings"), x)

  def closeEvent(self, ce):
    # stop any ongoing processes
    self.stopAction.activate()

    # save the configuration
    self.saveConfiguration()

    # destroy the downloaded covers
    self.coverview.clear()

    ce.accept()
    sys.exit(0)

  def walk(self, path):
    """Walk the given path and fill the album list with all the albums found."""

    try:
      if not isinstance(path, unicode):
        path = unicode(path, sys.getfilesystemencoding())
      # Get rid of any possible BOM
      path = path.lstrip(unicode(codecs.BOM_UTF8, "utf8"))
      self.dir = path

      # update the widget states
      self.setCursor(Qt.waitCursor)
      self.fileOpenAction.setEnabled(0)
      self.reloadAction.setEnabled(0)
      self.stopAction.setEnabled(1)

      # clear the db
      self.albums = {}
      self.stopped = False

      # if we are in 'folder' mode, we don't need to read anything yet
      if self.viewFoldersAction.isOn():
        return

      # check the cache
      try:
        (cachePath, cacheTime, cacheAlbums) = pickle.load(open(self.cachePath, "rb"))
      except:
        cachePath = None

      if cachePath == path and os.stat(path).st_mtime <= cacheTime:
        self.albums = cacheAlbums
      else:
        # no cache -> must walk the tree
        lastRepaintTime = time.time()
        for root, dirs, files in os.walk(path):
          if self.stopped:
            break
          for n in files:
            if self.stopped:
              break
            if os.path.splitext(n)[1].lower()[1:] in self.mediaExtensions:
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
        # save a fresh copy to the cache
        pickle.dump((path, time.time(), self.albums), open(self.cachePath, "wb"))
    finally:
      self.stopped = False
      self.stopAction.setEnabled(0)
      self.reloadAction.setEnabled(1)
      self.fileOpenAction.setEnabled(1)
      self.setCursor(Qt.arrowCursor)
      self.refreshAlbumList()
      self.statusBar().message(self.tr("%d items found. Ready.") % self.dirlist.childCount(), 5000)

  def refreshAlbumList(self):
    """Refreshes the album list according to the current search string."""
    self.dirlist.clear()

    if not self.dir:
      return

    try:
      self.setCursor(Qt.waitCursor)
      if self.viewFoldersAction.isOn():
        for fn in os.listdir(self.dir):
          if fn.startswith(".") or not self.matchesFilter(fn, "", ""):
            continue
          fullname = os.path.join(self.dir, fn)
          if os.path.isdir(fullname):
            FolderItem(self.dirlist, fullname, self.mediaExtensions)
          elif os.path.isfile(fullname) and os.path.splitext(fn)[1].lower()[1:] in self.mediaExtensions:
            FileItem(self.dirlist, fullname)
      else:
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
    finally:
      self.setCursor(Qt.arrowCursor)

  def matchesFilter(self, artist, album, tracks):
    """Tests whether the given artist, album or track list matches
       the current search filter."""
    query = self.getQString(self.filterEdit.text()).lower()
    if not query:
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
    AboutDialog(self).exec_loop()

  def fileOpen(self):
    d = self.getQString(
     QFileDialog.getExistingDirectory(
       self.dir, self,
       self.tr("Choose a directory that contains one or more albums"),
       self.tr("Choose a directory"),
       1))
    if d and len(d):
      self.walk(d)

  def reloadAction_activated(self):
    # invalidate the cache
    try:
      os.unlink(self.cachePath)
    except:
      pass

    if len(self.dir):
      self.walk(self.dir)

  def removeAction_activated(self):
    if QMessageBox.information(self,
         self.tr("Confirm deletion"),
         self.tr("Are you sure you want to delete the selected cover images?"),
         QMessageBox.Yes + QMessageBox.Default,
         QMessageBox.No + QMessageBox.Escape) == QMessageBox.Yes:
      self.setCursor(Qt.waitCursor)
      self.statusBar().message("Deleting selected cover images...")

      for item in self.getSelectedItems():
        try:
          albumart.removeCover(item.getPath())
        except Exception, x:
          self.reportException(self.tr("Removing cover images"), x)

      [item.refresh() for item in self.getSelectedItems()]
      self.setCursor(Qt.arrowCursor)
      self.statusBar().message("Ready", 5000)

  def selectAllAction_activated(self):
    self.dirlist.selectAll(True)

  def startProcess(self, process):
    """Runs the given process instance. @see process.Process"""
    self.progressWidget = ProgressWidget(self)
    self.progressWidget.textLabel.setText(process.__doc__)
    self.thread = process
    self.connect(self.progressWidget.buttonCancel, SIGNAL("clicked()"), self.processCanceled)
    self.statusBar().clear()
    self.statusBar().addWidget(self.progressWidget)
    self.thread.start()

  def processCanceled(self):
    """Cancels the active process"""
    self.statusBar().removeWidget(self.progressWidget)
    self.progressWidget.close()
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
    items = [item.getPath() for item in self.getSelectedItems() if not albumart.hasCover(item.getPath())]
    self.setCursor(Qt.arrowCursor)
    self.statusBar().message("")
    self.startProcess(AutoDownloadProcess(self, self.dir, items, self.requireExactMatch))

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
    flag = len(self.getSelectedItems(expand = False)) > 0
    self.autoDownloadAction.setEnabled(flag)
    self.removeAction.setEnabled(flag)
    self.viewCoverAction.setEnabled(flag)
    self.pushSet.setEnabled(0)

  def dirlist_currentChanged(self, a0):
    try:
      self.artistEdit.setText(a0.getArtistName())
      self.albumEdit.setText(a0.getAlbumName())
    except AttributeError:
      self.artistEdit.setText("")
      self.albumEdit.setText("")

    # clean up the previous cover items
    for item in self.currentCoverItems:
      try:
        self.coverview.takeItem(item)
      except:
        pass
    self.currentCoverItems = []
    # add new ones for this item
    for f in self.scanItemForCovers(a0):
      self.currentCoverItems.append(self.addCoverToList(f.path.encode(sys.getfilesystemencoding()))) 

  def scanItemForCovers(self, item):
    """Scans the given item for cover images and the
       resulting list of filenames."""
    files = []
    if albumart.hasCover(item.getPath()):
      cover = albumart.getCover(item.getPath())
      if cover: files.append(cover)
    if os.path.isdir(item.getPath()):
      for f in os.listdir(item.getPath()):
        try:
          # don't add the built-in defaults
          if f in [".folder.png", "folder.jpg"]:
            continue
          f = os.path.join(item.getPath(), f)
          if f in files:
            continue
          i = QImage(f)
          if not i.isNull():
            files.append(albumart.Cover(f))
        except:
          pass
    return files

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
    return unicode(qstring).encode(sys.getfilesystemencoding(), "replace")

  def getSelectedItems(self, expand = True):
    """@returns a list of selected media items to process"""
    items = []

    def addSelectedChildren(item, force = False):
      if item.isSelected() or force:
        items.append(item)
        if expand: item.setOpen(True)
      child = item.firstChild()
      while child:
        addSelectedChildren(child, item.isSelected() or force)
        child = child.nextSibling()

    item = self.dirlist.firstChild()
    while item:
      addSelectedChildren(item, item.isSelected())
      item = item.nextSibling()

    return items

  def addCoverToList(self, coverfile, delete = False, linkUrl = None, linkText = None):
    """Adds the given cover to the list of available album covers.
       @returns the cover item or None on error."""
    try:
      image = QImage(coverfile)
    except IOError:
      return None

    if not image.isNull() and image.width() > 1 and image.height() > 1:
      text = str(imghdr.what(str(coverfile))).upper() + " Image - %dx%d pixels" % (image.width(), image.height())
      image = image.smoothScale(256, 256, QImage.ScaleMin)
      return CoverItem(self.coverview, QPixmap(image), coverfile, delete, text = text, linkUrl = linkUrl, linkText = linkText)

  def customEvent(self, event):
    """Handle events from processes"""
    # if the message was sent by an older thread, ignore it.
    if self.__dict__.has_key("thread"):
      if self.thread != event.thread:
        return

    if event.type() == CoverDownloadedEvent.id:
      self.addCoverToList(event.cover.path, delete = True, linkUrl = event.cover.linkUrl, linkText = event.cover.linkText)
    elif event.type() == TaskFinishedEvent.id:
      if os.name == "nt":
        # For some reason threads don't always terminate with Q..3/Windows Edition
        self.thread.terminate()
        self.thread.wait(500)
      else:
        self.thread.wait()
      self.thread = None
      self.statusBar().removeWidget(self.progressWidget)
      self.progressWidget.close()

      if event.message:
        QMessageBox.information(self, version.__program__,event.message)

      self.pushDownload.setEnabled(1)
    elif event.type() == ExceptionEvent.id:
      self.reportException(self.tr("Downloading cover images"),
                           event.exception,
                           description = event.description)
    elif event.type() == ProgressEvent.id:
      if self.progressWidget:
        self.progressWidget.progressBar.setTotalSteps(event.total)
        self.progressWidget.progressBar.setProgress(event.progress)
    elif event.type() == StatusEvent.id:
      if self.progressWidget:
        self.progressWidget.textLabel.setText(event.text)
    elif event.type() == ReloadEvent.id:
      [item.refresh() for item in self.getSelectedItems()]

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
      d.setPixmap(resizePixmap(self.coverview.currentItem().pixmap(), 64))
      return d

  def pushSet_clicked(self):
    self.setCover(self.coverview.currentItem().getPath())

  def setCover(self, coverPath):
    return self.setCoverForItems(coverPath, self.getSelectedItems())

  def setCoverForItems(self, coverPath, items):
    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Setting cover images..."))

    for item in items:
      try:
        albumart.setCover(item.getPath(), albumart.Cover(coverPath))
        self.statusBar().message(self.tr("Writing %s") % os.path.basename(item.getPath()))
        item.refresh()
        qApp.processEvents()
      except Exception, x:
        self.reportException(self.tr("Setting the cover image"), x)

    self.setCursor(Qt.arrowCursor)
    self.statusBar().message(self.tr("Ready"), 5000)

  def decodeDropEventAsCover(self, event):
    """@returns a file name for the given cover drop event or None or error.
       Remember to clean up the file returned by this function."""
    if QTextDrag.canDecode(event):
      s = QString()
      if QTextDrag.decode(event, s):
        url = self.getQString(s).strip()
        # decode weird drag'n'drop data formats
        if "\n" in url: url = url.split("\n")[0]
        if url.startswith("file:///") and os.path.exists(url[8:]): url = url[8:]
        if os.path.exists(url): url = "file:" + url
        f = urllib.urlopen(url)
        fn = tempfile.mktemp()

        # write to a temporary file
        o = open(fn, "wb")
        o.write(f.read())
        o.close()

        # convert to JPEG
        img = Image.open(fn)
        img.load()
        img = img.convert("RGB")
        img.save(fn, "JPEG", quality = 100)
        return albumart.Cover(fn)

  def dirlist_dropEvent(self, event):
    # check whether it is a path
    if QTextDrag.canDecode(event):
      s = QString()
      if QTextDrag.decode(event, s):
        url = urllib.unquote(self.getQString(s)).strip()
        if url.startswith("file:///") and os.path.isdir(url[8:]): url = url[8:]
        elif url.startswith("file:"): url = url[len("file:"):]
        if os.path.isdir(url):
          self.walk(url)
          return

    try:
      fn = self.decodeDropEventAsCover(event)
      if fn:
        event.accept(True)

        item = self.dirlist.itemAt(event.pos())
        if item:
          items = [item]
          if isinstance(item, AlbumItem) or isinstance(item, FolderItem):
            item.setOpen(True)
            def addChildren(item):
              child = item.firstChild()
              while child:
                if isinstance(child, FileItem) or isinstance(child, TrackItem):
                  items.append(child)
                child = child.nextSibling()
            addChildren(item)
          self.setCoverForItems(fn.path, items)

        os.unlink(fn.path)
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
    return self.getQString(QObject.tr(self, identifier, context))

  def coverview_dropped(self, event, a1):
    try:
      fn = self.decodeDropEventAsCover(event)
      if fn:
        self.addCoverToList(fn.path, delete = True)
    except Exception, x:
      self.reportException(self.tr("Adding the cover image"), x)

  def showConfigurationDialog(self):
    c = ConfigurationDialog(self, [self] + self.modules)
    if c.exec_loop() == QDialog.Accepted:
      self.saveConfiguration()

  def stopAction_activated(self):
    self.stopAction.setEnabled(0)
    self.stopped = True

  def viewFoldersAction_activated(self):
    if not self.viewFoldersAction.isOn():
      self.viewFoldersAction.setOn(True)
    self.viewAlbumsAction.setOn(False)
    self.refreshAlbumList()

  def viewAlbumsAction_activated(self):
    if not self.viewAlbumsAction.isOn():
      self.viewAlbumsAction.setOn(True)
    self.viewFoldersAction.setOn(False)
    if self.dir:
      self.walk(self.dir)
    self.refreshAlbumList()

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
from event import *
from process import *

# see if we're using an old Qt version
if qVersion().split(".")[0] == "2":
  from albumartdialog_qt230 import AlbumArtDialog
else:
  from albumartdialog import AlbumArtDialog
  
import albumartimages

# empty cover pixmap
noCoverPixmap = None

#
# @returns a QPixmap representing the given path
#
def getPixmapForPath(path):
  global noCoverPixmap
  
  if not noCoverPixmap:
    noCoverPixmap = QPixmap()
    img = QImage()
    QImageDrag.decode(albumartimages.MimeSourceFactory_albumart().data(QString("nocover.png")), img)
    noCoverPixmap.convertFromImage(img)

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
            return noCoverPixmap
      else:
          pixmap = QPixmap(filename)
          
      if pixmap.width() > 0 and pixmap.height() > 0:
        return pixmap
      else:
        return noCoverPixmap
  return noCoverPixmap
  
def resizePixmap(pixmap, size, width = None, height = None):
  if not pixmap.isNull() and pixmap.width() > 0 and pixmap.height() > 0:
    if not width and not height:
      width = height = size
    p = QPixmap()
    try:
      p.convertFromImage(pixmap.convertToImage().scale(width, height))
    except AttributeError:
      # for older Qt 2.x
      p.convertFromImage(pixmap.convertToImage().smoothScale(width, height))
    pixmap = p
  return pixmap
  
#
# A track list item
#  
class TrackItem(QListViewItem):
  def __init__(self, album, path):
    QListViewItem.__init__(self, album)
    self.setDropEnabled(True)
    self.path = path
    self.name = os.path.basename(path)
    self.margin = 8
    self.album = album

  def paintCell(self, painter, colorGroup, column, width, alignment):
    if not self.pixmap(0):
      self.refresh()
      
    if self.isSelected():
      painter.fillRect(0, 0, width, self.height(), QBrush(colorGroup.mid().light(120)))
    else:
      painter.eraseRect(0, 0, width, self.height())

    m = self.listView().itemMargin()
    painter.drawPixmap(m, 0, self.pixmap(0))
    painter.drawText(2 * m + self.pixmap(0).width(), m, 
                     width, self.height(), 0, self.name)
    
  def paintFocus(self, painter, colorGroup, rect):
    pass

  def acceptDrops(self, mimeSource):
    return True

  def refresh(self):
    self.setPixmap(0, resizePixmap(getPixmapForPath(self.path), 22))
        
  def width(self, fontMetrics, listView, column):
    if self.pixmap(0):
      return self.pixmap(0).width() + fontMetrics.width(self.name) + 16
    return 0
    
  #
  # @returns the album name
  #
  def getAlbumName(self):
    return self.album.getAlbumName()

  #
  # @returns the artist name
  #
  def getArtistName(self):
    return self.album.getArtistName()

  #
  # @returns the path for this item
  #
  def getPath(self):
    return self.path
                  
#
# An album list item
#  
class AlbumItem(QListViewItem):
  def __init__(self, parent, path, artist, album):
    QListViewItem.__init__(self, parent)
    self.setDropEnabled(True)
    self.path = path
    self.artist = artist
    self.album = album
    self.tracks = []
    self.margin = 8
    self.iconSize = 64
    self.openTrigger = QRect()
    self.titleFont = QFont(QFont().family(), QFont().pointSize() + 3, QFont.Bold)

  def acceptDrops(self, mimeSource):
    return True
    
  def refresh(self):
    self.setPixmap(0, resizePixmap(getPixmapForPath(self.path), self.iconSize))
    
  def paintCell(self, painter, colorGroup, column, width, alignment):
    if not self.pixmap(0):
      self.refresh()

    if self.isSelected():
      painter.fillRect(0, 0, width, self.height(), QBrush(colorGroup.mid().light(120)))
    else:
      painter.eraseRect(0, 0, width, self.height())

    # draw the icon    
    m = self.listView().itemMargin()
    painter.drawPixmap(m + self.margin, m + self.margin, self.pixmap(0))
    m += 4
      
    left = self.pixmap(0).width() + m + self.margin
    painter.setPen(colorGroup.text())
    fontSize = painter.font().pointSize()
    
    # draw the album title
    painter.setFont(self.titleFont)
    painter.drawText(left, m + self.margin, 
                     width, self.height(), 0, self.album)
    titleRect = painter.boundingRect(0, 0, width, self.height(), 0, self.album)
    
    # draw the artist name
    subtitleRect = painter.boundingRect(0, 0, width, self.height(), 0, self.artist)
    painter.setFont(QFont(painter.font().family(), fontSize))
    painter.drawText(left, m + self.margin + titleRect.height(), 
                     width, self.height() / 2, 0, self.artist)

    # draw the open indicator
    painter.setPen(colorGroup.mid())
    painter.setBrush(colorGroup.mid())
    smallFontSize = fontSize - 1
    arrow = QPointArray(3)
    if self.isOpen():
      arrow.setPoint(0, 0, smallFontSize / 2 + 2)
      arrow.setPoint(1, smallFontSize, smallFontSize / 2 + 2)
      arrow.setPoint(2, smallFontSize / 2, smallFontSize + 2)
    else:
      arrow.setPoint(0, smallFontSize / 4, 0 + 2)
      arrow.setPoint(1, 3 * smallFontSize / 4, smallFontSize / 2 + 2)
      arrow.setPoint(2, smallFontSize / 4, smallFontSize + 2)
    self.openTrigger.setRect(left, m + self.margin + titleRect.height() + m + subtitleRect.height(),
                             smallFontSize, smallFontSize)
    painter.translate(self.openTrigger.left(), self.openTrigger.top())
    painter.drawPolygon(arrow)
                     
    # draw the track count
    painter.setFont(QFont(painter.font().family(), smallFontSize))
    text = str(len(self.tracks)) + (len(self.tracks) == 1 and " track" or " tracks")
    painter.drawText(self.openTrigger.width() + m, 0,
                     width, self.height() / 2, 0, text)
    
  def paintFocus(self, painter, colorGroup, rect):
    pass
    
  def paintBranches(self, painter, colorGroup, w, y, h, style = None):
    painter.eraseRect(0, 0, w, h)

  def width(self, fontMetrics, listView, column):
    return self.pixmap(0).width() + QFontMetrics(self.titleFont).width(self.album) + 16
    
  def setup(self):
    self.setHeight(self.iconSize + self.margin * 2)
    
  def activate(self):
    # open the album if the cursor is within the trigger
    p = self.listView().mapFromGlobal(QCursor.pos())
    p.setY(p.y() - self.itemPos() + self.listView().contentsY())
    if p.y() >= self.openTrigger.top() and \
       p.x() > self.openTrigger.left() - 4 and \
       p.x() < self.openTrigger.right() + 4:
      self.setOpen(not self.isOpen())
      
  #
  # @returns the album name
  #
  def getAlbumName(self):
    return self.album

  #
  # @returns the artist name
  #
  def getArtistName(self):
    return self.artist
            
  #
  # Add a new track to this album
  #
  def addTrack(self, fileName):
    if not fileName in self.tracks:
      self.tracks.append(fileName)
    return TrackItem(self, fileName)
  
  #
  # @returns the path for this item
  #
  def getPath(self):
    return self.path
    
#
# A cover image item
#    
class CoverItem(QIconViewItem):
  def __init__(self, parent, pixmap, path):
    QListViewItem.__init__(self, parent, "", pixmap)
    self.margin = 6
    self.path = path
    self.setItemRect(QRect(0, 0,
                     self.pixmap().width() + self.margin * 2,
                     self.pixmap().height() + self.margin * 2))
                     
  def __del__(self):
    # delete the temporary file
    try:
      os.unlink(self.path)
    except:
      pass
                     
  #
  # @returns the path for this item
  #
  def getPath(self):
    return self.path
                         
  def paintFocus(self, painter, colorGroup):
    pass
    
  def paintItem(self, painter, colorGroup):
    if self.isSelected():
      painter.setBrush(colorGroup.mid().light(120))
      painter.setPen(colorGroup.dark())
      painter.drawRoundRect(self.x(), self.y(),
                            self.width(), self.height(),
                            self.margin, self.margin)
      
    painter.drawPixmap(self.x() + self.margin,
                       self.y() + self.margin, self.pixmap())

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
               name = "AlbumArtUi",
               fl = 0,
               dataPath = ".",
               albumPath = None):
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
    self.dirlist.__class__.dragObject = self.dirlist_dragObject
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
    
  #
  # Load the settings from the configuration file
  #    
  def loadConfiguration(self):
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
      self.config.set("albumart", "recognizers",
                      "albumart_recognizer_id3v2.ID3v2Recognizer:" +
                      "albumart_recognizer_path.PathRecognizer")
      # global settings
      self.settingsMenu.clear()
      try:
        self.showCoversAction.setOn(self.config.getboolean("albumart", "showcovers"))
      except Exception,x:
        self.showCoversAction.setOn(True)

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

  #
  #  @returns the given pixmap scaled to icon size
  #                          
  def scaleIconPixmap(self, pixmap):
    return self.scalePixmap(pixmap, self.iconSize)

  #
  #  @returns the given pixmap scaled to a new size
  #  @param size New pixel size.
  #
  def scalePixmap(self, pixmap, size):
    if not pixmap.isNull() and pixmap.width() > 0 and pixmap.height() > 0:
      try:
        pixmap.convertFromImage(pixmap.convertToImage().scale(size, size))
      except AttributeError:
        # for older Qt 2.x
        pixmap.convertFromImage(pixmap.convertToImage().smoothScale(size, size))
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
      
  #
  # Load a module with the given name (id)
  #      
  def loadModule(self, id):
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
          if desc[0]=="boolean":
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
      
  #
  # Reports the given exception to the user.
  #
  # @param task Description of task during which the exception was raised
  # @param exception The exception that was raised
  # @param silent Pass True if a dialog box shouldn't be shown.
  # @param description An optional description of the exception.
  #        If not given, the description is generated from the system stack.
  #
  def reportException(self, task, exception, silent = False, description = None):
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

    # first save the folder as an album
    #(artist, album) = albumart.guessArtistAndAlbum(dirname)
    #album = AlbumItem(self.dirlist, artist, album)
    #album.setPixmap(0, self.getIconForPath(path))
    #self.albums[(artist, album)] = album
    
    #dirname=dirname.replace(root,"")
    #if not len(dirname):
    #  dirname="."

    #item = QListViewItem(self.dirlist, dirname, artist, album)
    
    lastRepaintTime = time.time()

    # add each file in the directory to it's respective album
    for n in names:
      if os.path.splitext(n)[1].lower() in albumart.mediaExtensions:
        # update status bar often enough
        if time.time() > lastRepaintTime + 0.1:
          self.statusBar().message(self.tr("Reading %s") % n)
          lastRepaintTime = time.time()
          qApp.processEvents()
        p = os.path.join(path, n)
        (artist, album) = albumart.guessArtistAndAlbum(p)
        
        # get the album for this track
        if not (artist, album) in self.albums:
          a = AlbumItem(self.dirlist, os.path.dirname(p), artist, album)
          
          #if albumart.hasCover(p):
          #  a.loadIcon = lambda: self.getIconForPath(p)
          #  #a.setPixmap(0, self.getIconForPath(p))
          #else:
          #  a.loadIcon = lambda: self.getIconForPath(path)
          #  #a.setPixmap(0, self.getIconForPath(path))
          #a.setPixmap(0, getPixmapForPath(""))
          
          self.albums[(artist, album)] = a
        else:
          a = self.albums[(artist, album)]
        
        # add the track to the album 
        t = a.addTrack(p)
        t.loadIcon = lambda: self.scalePixmap(self.getPixmapForPath(p), 16)
        #pixmap = self.scalePixmap(self.getPixmapForPath(p), 16)
        #t.setPixmap(0, pixmap)

  #
  # Walk the given path and fill the album list with all the albums found.
  #
  def walk(self, path):
    self.dir = path
    
    # update the widget states
    self.fileOpenAction.setEnabled(0)
    self.reloadAction.setEnabled(0)
    self.dirlist.clear()
    
    # clear the db
    self.albums = {}
    
    self.setCursor(Qt.waitCursor)
    os.path.walk(path, self.process, path)
    self.statusBar().message(self.tr("%d albums found. Ready.") % (self.dirlist.childCount()), 5000)
    self.setCursor(Qt.arrowCursor)

    self.reloadAction.setEnabled(1)
    self.fileOpenAction.setEnabled(1)
    
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
    if qVersion().split(".")[0] == "2":
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
  # Either the album or artists edit boxes were modified
  #
  def queryEdited(self):
    self.pushDownload.setEnabled(
      not self.albumEdit.text().isEmpty() or \
      not self.artistEdit.text().isEmpty())

  #
  # Download images automatically for all the albums
  #
  def autoDownloadAction_activated(self):
    item = self.dirlist.firstChild()

    self.setCursor(Qt.waitCursor)
    self.statusBar().message(self.tr("Preparing automatic download..."))
    items = [file for file in self.getSelectedFiles() if not albumart.hasCover(file)]
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
    
  #
  # @returns a python string representation of the given QString
  #
  def getQString(self, qstring):
    return unicode(qstring).encode("latin-1", "replace")

  def albumIcon_clicked(self):
    # Try to load the current album cover image and display it in as new window
    try:
      path = os.path.join(self.dir,self.getQString(self.selectedItem.text(0)))
      pixmap = self.getPixmapForPath(path)
      self.coverPreviewWindow = QLabel(None)
      self.coverPreviewWindow.setPixmap(pixmap)
      self.coverPreviewWindow.setFixedSize(pixmap.width(), pixmap.height())
      self.coverPreviewWindow.setCaption(
        self.tr("Cover image for %(album)s") % \
        {"album" : self.getQString(self.selectedItem.text(0))})
      self.coverPreviewWindow.show()
    except Exception, x:
      self.reportException(self.tr("Loading the album cover"), x)
      
  #
  #  @returns a list of selected media files to process
  #
  def getSelectedFiles(self):
    # return each selected track's path
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

  #
  #  @returns a list of current (i.e. focused) media files to process
  #
  def getCurrentFiles(self):
    # return each selected track's path
    item = self.dirlist.currentItem()
    files = [item.getPath()]
    
    if isinstance(item, AlbumItem):
      trackItem = item.firstChild()
      while trackItem:
        files.append(trackItem.getPath())
        trackItem = trackItem.nextSibling()
    return files
    
  #
  # Reloads icons for the selected files
  #
  def refreshSelectedFiles(self):
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
    
  #
  # Adds the given cover to the list of available album covers.
  #
  def addCoverToList(self, coverfile):
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

  #
  # Handle events from processes
  #        
  def customEvent(self, event):
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
        
    self.refreshSelectedFiles()
    self.setCursor(Qt.arrowCursor)
    self.statusBar().message(self.tr("Ready"), 5000)

  def dirlist_dragObject(self):
    return self.dirlist.currentItem().getPath()
    
  #
  # @returns a file name for the given cover drop event or None or error.
  # Remember to clean up the file returned by this function.
  #
  def decodeDropEventAsCover(self, event):
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
        img.save(fn, "JPEG")
        return fn
  
  def dirlist_dropEvent(self, event):
    try:
      fn = self.decodeDropEventAsCover(event)
      if fn:
        self.setCoverForCurrentFiles(fn)
        os.unlink(fn)
        event.accept(True)
    except Exception, x:
      self.reportException(self.tr("Setting the cover image"), x)
  
  def dirlist_dragEnterEvent(self, event):
    if QTextDrag.canDecode(event):
      event.accept()

  def viewCoverImage(self):
    # Try to load the current album cover image and display it in as new window
    try:
      pixmap = getPixmapForPath(self.dirlist.currentItem().getPath())
      global window
      window = QLabel(None)
      window.setPixmap(pixmap)
      window.setFixedSize(pixmap.width(), pixmap.height())
      window.show()
    except Exception, x:
      self.reportException(self.tr("Loading the album cover"), x)
    
    
  def setFilter(self, filterString):
    filterString = self.getQString(filterString)
    if self.filterEdit.palette().active().text() != self.palette().active().text():
      self.filterEdit.clear()
      self.filterEdit.setPalette(self.palette())

  #
  # Overridden translation method that returns native Python strings
  #  
  def tr(self, identifier, context = None):
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

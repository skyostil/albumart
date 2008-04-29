from qt import *
from event import *
import albumart
import Image
import version
import traceback
import sys
import os

class Process(QThread):
  """An asynchronous process for doing lengthy operations."""
  def __init__(self, dialog):
    """Constructor.
    
       @param dialog The QObject that will receive events via postEvent
                     Warning: The given QObject should have a tr() method that
                     returns native Python strings."""
    QThread.__init__(self)
    self.dialog = dialog
    self.canceled = 0

  def cancel(self):
    self.canceled = 1

  def isCanceled(self):
    return self.canceled

  def setProgress(self, progress, total):
    self.postEvent(self.dialog, ProgressEvent(self, progress, total))

  def setStatusText(self, text):
    self.postEvent(self.dialog, StatusEvent(self, text))
    
  def setComplete(self, message = None, result = True):
    self.postEvent(self.dialog, TaskFinishedEvent(self, message, result))

  def triggerReload(self):
    self.postEvent(self.dialog, ReloadEvent(self))

  def run(self):
    pass

class CoverDownloaderProcess(Process):
  """Cover Download"""
  def __init__(self,dialog,artist,album):
    Process.__init__(self, dialog)
    self.artist = artist
    self.album = album

  def run(self):
    coversFound = 0
    if self.album and self.artist and len(self.album) and len(self.artist):
      self.setStatusText(self.dialog.tr("Searching images for '%(album)s' by %(artist)s...") % \
                         {"album" : self.album, "artist" : self.artist})
    elif len(self.album):
      self.setStatusText(self.dialog.tr("Searching images for the album '%(album)s'...") % \
                         {"album" : self.album})
    elif len(self.artist):
      self.setStatusText(self.dialog.tr("Searching images for the artist %(artist)s...") % \
                         {"artist" : self.artist})
      
    try:
      for c in albumart.getAvailableCovers(self.artist, self.album):
        coversFound += 1
        if self.isCanceled():
          break
          
        img = Image.open(c.path)
        img.load()
        
        # convert to JPEG if needed
        if img.format != "JPEG":
            img = img.convert("RGB")
            img.save(c.path)
          
        self.postEvent(self.dialog, CoverDownloadedEvent(self, c))
        # better fake progress than none at all :)
        # we can't tell how many covers we've
        # downloaded as they may have been blank or
        # corrupt.
        self.setProgress(coversFound - 1,coversFound)
    except Exception, x:
      self.postEvent(self.dialog, ExceptionEvent(self, x))

    if coversFound > 0:
      self.setComplete()
    else:
      self.setComplete(
        self.dialog.tr("Sorry, no cover images were found. Try simpler keywords. \n" +
                       "However, if you already have a cover image you'd like to use, \n" +
                       "go ahead drop it on the cover image list."))

class AutoDownloadProcess(Process):
  """Automatic Cover Download"""
  def __init__(self, dialog, dir, items, requireExactMatch):
    Process.__init__(self, dialog)
    self.items = items
    self.dir = dir
    self.requireExactMatch = requireExactMatch

  def run(self):
    itemsProcessed = 0
    recognized = 0
    coversFound = 0
    coversInstalled = 0
    failures = 0
    cache = {}
    
    try:
      for path in self.items:
        if self.isCanceled():
          failures = -1
          break

        (artist, album) = albumart.guessArtistAndAlbum(path)

        if artist and album:
          recognized += 1
          self.setStatusText(self.dialog.tr('Searching cover for "%(album)s" by %(artist)s...') % \
                             {"album" : album, "artist" : artist})
          if cache.has_key((artist, album)):
            try:
              albumart.setCover(path, cache[(artist, album)])
              coversInstalled += 1
            except Exception, x:
              failures += 1
              traceback.print_exc(file = sys.stderr)
          else:
            foundAny = False
            for cover in albumart.getAvailableCovers(artist, album, requireExactMatch = self.requireExactMatch):
              foundAny = True
              try:
                img = Image.open(cover.path)
                img.load()
                coversFound += 1

                # convert to JPEG if needed
                if img.format != "JPEG":
                  img = img.convert("RGB")
                  img.save(cover.path)

                cache[(artist, album)] = cover
                albumart.setCover(path, cover)
                coversInstalled += 1
              except Exception, x:
                failures += 1
                traceback.print_exc(file = sys.stderr)
              break
            if not foundAny:
              failures += 1
        itemsProcessed += 1
        self.setProgress(itemsProcessed, len(self.items))
    except Exception, x:
      self.postEvent(self.dialog, ExceptionEvent(self, x))
    self.triggerReload()
    
    # clear the cache
    for cover in cache.values():
      os.unlink(cover.path)
    
    self.setComplete(
      self.dialog.tr(
        "Out of a total of %d items, %d were recognized, \n" +
        "%d matching covers were found and \n" +
        "%d were installed.") % \
      (len(self.items), recognized, coversFound, coversInstalled),
      result = (failures == 0))

class SynchronizeProcess(Process):
  """Cover Image Synchronization"""
  def __init__(self, dialog, dir, items):
    Process.__init__(self, dialog)
    self.items = items
    self.dir = dir

  def run(self):
    itemsProcessed = 0
    
    for path in self.items:
      if self.isCanceled():
        break

      self.setStatusText(self.dialog.tr('Synchronizing %s...') % \
                         (path.replace(self.dir,"")))
      albumart.synchronizeCovers(path)

      itemsProcessed += 1
      self.setProgress(itemsProcessed, len(self.items))

    self.triggerReload()
    self.setComplete()

class DeleteProcess(Process):
  """Cover Image Deletion"""
  def __init__(self, dialog, dir, items):
    Process.__init__(self, dialog)
    self.items = items
    self.dir = dir

  def run(self):
    itemsProcessed = 0
    
    errors = []
    for path in self.items:
      if self.isCanceled():
        break

      if albumart.hasCover(path):
        self.setStatusText(self.dialog.tr('Deleting cover from %s...') % \
                           (path.replace(self.dir, "")))
        try:
          albumart.removeCover(path)
        except Exception,x:
          traceback.print_exc(file = sys.stderr)
          errors.append(str(x))

      itemsProcessed += 1
      self.setProgress(itemsProcessed, len(self.items))

    self.triggerReload()
    
    if len(errors):
      errors = "\n".join(errors)
      self.setComplete(
        self.dialog.tr("The following error(s) occured while removing the cover images: \n%s") % \
                       errors)
    else:
      self.setComplete()

# -*- coding: iso-8859-1 -*-
#
# Unattended front-end to the album cover downloader.
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
import ConfigParser
from qt import *

# local imports
import albumart
import version
import config
from event import *
from process import *

class AlbumArtUnattendedUi(QWidget):
  #
  # Constructor. 
  #
  # @param parent Parent widget
  # @param name Widget name
  # @param showSummary Show a summary dialog when done.
  #
  def __init__(self, parent = None,
               name = "AlbumArtUnattendedUi",
               showSummary = False,
               hidden = False):
    QObject.__init__(self, parent, name)
    self.config = ConfigParser.ConfigParser()
    self.showSummary = showSummary
    self.hidden = hidden
    
    try:
      # load the configuration
      fn = os.path.join(config.getConfigPath("albumart"), "config")
      self.config.read(fn)
  
      if not self.config.has_section("albumart"):
        raise RuntimeError(
          self.tr("Album Cover Art Downloader has not been configured yet. " +
                  "Please run it in standard mode first."))
                  
      for s in self.config.get("albumart", "sources").split(":"):
        mod = self.loadModule(s)
        albumart.addSource(mod)
  
      for t in self.config.get("albumart", "targets").split(":"):
        mod = self.loadModule(t)
        albumart.addTarget(mod)
        
      for t in self.config.get("albumart", "recognizers").split(":"):
        mod = self.loadModule(t)
        albumart.addRecognizer(mod)
    except Exception, x:
      self.reportException(self.tr("Loading settings"), x)
  
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
      c.configure(cfg)
      return c
    except Exception, x:
      self.reportException(self.tr("Loading module '%s'") % (id), x)
      
  #
  # Reports the given exception to the user.
  #
  # @param task Description of task during which the exception was raised
  # @param exception The exception that was raised
  #
  def reportException(self, task, exception):
    xcpt = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    msg = self.tr(
            "%(task)s was interrupted by the following exception:\n%(xcpt)s\n") % \
            {"task" : task, "xcpt": "".join(xcpt)}
    sys.stderr.write(msg)

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

    if not self.hidden:
      self.progressDialog.show()
    self.thread.start()

  #
  # Cancels the active process
  #
  def processCanceled(self):
    if self.thread:
      self.thread.cancel()

  #
  # Download images automatically for the given path
  #
  def downloadCovers(self, path):
    items = self.getItems(path)
    items = filter(lambda i: not albumart.hasCover(i), items)
    self.startProcess(AutoDownloadProcess(self, path, items))

  #
  # Make sure all the albums have same images in all their targets
  # (fd.o, wxp, id3v2, etc.)
  #
  def synchronizeCovers(self, path):
    items = self.getItems(path)
    items = filter(lambda i: albumart.hasCover(i), items)
    self.startProcess(SynchronizeProcess(self, path, items))

  #
  # Delete all cover images below the given path
  #
  def deleteCovers(self, path):
    items = self.getItems(path)
    self.startProcess(DeleteProcess(self, path, items))

  #
  # Handle events from processes
  #        
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
        print event.message.replace("\n", "")
        if self.showSummary:
          QMessageBox.information(self, version.__program__, event.message)
      
      QApplication.exit(not event.result)

    elif event.type() == ExceptionEvent.id:
      self.reportException(self.tr("Downloading cover images"), event.exception)
    elif event.type() == ProgressEvent.id:
      if self.progressDialog and not self.hidden:
        self.progressDialog.setTotalSteps(event.total)
        self.progressDialog.setProgress(event.progress)
    elif event.type() == StatusEvent.id:
      if self.progressDialog and not self.hidden:
        self.progressDialog.setLabelText(event.text)
    elif event.type() == ReloadEvent.id:
      pass

    del event
    
  #
  # Returns a list of processable items under the given path
  #
  def getItems(self, path):
    items = []
    for root, dirs, files in os.walk(path):
      items.append(root)
    return filter(lambda x: not os.path.basename(x).startswith("."), items)

  #
  # @returns a python string representation of the given QString
  #
  def getQString(self, qstring):
    return unicode(qstring).encode("latin-1", "replace")
    
  #
  # Overridden translation method that returns native Python strings
  #  
  def tr(self, identifier, context = None):
    if qVersion().split(".")[0] == "2":
      # tr is static in old Qt
      return self.getQString(QObject.tr(identifier, context))
    return self.getQString(QObject.tr(self, identifier, context))

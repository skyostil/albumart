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

# use the configuration from the main program
from albumart_dialog import defaultConfig, configDesc

class AlbumArtUnattendedUi(QWidget):
  def __init__(self, parent = None,
               name = "AlbumArtUnattendedUi",
               showSummary = False,
               hidden = False):
    """Constructor. 
       @param parent Parent widget
       @param name Widget name
       @param showSummary Show a summary dialog when done."""
    QObject.__init__(self, parent, name)
    self.modules = []
    self.config = ConfigParser.RawConfigParser()
    self.showSummary = showSummary
    self.hidden = hidden
    self.loadConfiguration()

  def configure(self, config):
    # some day we might find the plugins dynamically
    for c in ["sources", "targets", "recognizers"]:
      config[c] = defaultConfig[c]

    self.requireExactMatch = config["require_exact_match"]
    
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
        raise RuntimeError(
          self.tr("Album Cover Art Downloader has not been configured yet. " +
                  "Please run it in standard mode first."))
      config.configureObject(self, self.config, "albumart_dialog")
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
      
  def reportException(self, task, exception):
    """Reports the given exception to the user.
    
       @param task Description of task during which the exception was raised
       @param exception The exception that was raised"""
    xcpt = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    msg = self.tr(
            "%(task)s was interrupted by the following exception:\n%(xcpt)s\n") % \
            {"task" : task, "xcpt": "".join(xcpt)}
    sys.stderr.write(msg)

  def startProcess(self, process):
    """Runs the given process instance. @see process.Process"""
    self.progressDialog = QProgressDialog(self, "progress", 1)
    self.progressDialog.setCaption(process.__doc__)
    self.thread = process
    self.progressDialog.connect(self.progressDialog, SIGNAL("canceled()"), self.processCanceled)

    if not self.hidden:
      self.progressDialog.show()
    self.thread.start()

  def processCanceled(self):
    """Cancels the active process"""
    if self.thread:
      self.thread.cancel()

  def downloadCovers(self, path):
    """Download images automatically for the given path"""
    items = self.getItems(path)
    items = filter(lambda i: not albumart.hasCover(i), items)
    self.startProcess(AutoDownloadProcess(self, path, items, self.requireExactMatch))

  def synchronizeCovers(self, path):
    """Make sure all the albums have same images in all their targets
      (fd.o, wxp, id3v2, etc.)"""
    items = self.getItems(path)
    items = filter(lambda i: albumart.hasCover(i), items)
    self.startProcess(SynchronizeProcess(self, path, items))

  def deleteCovers(self, path):
    """Delete all cover images below the given path"""
    items = self.getItems(path)
    self.startProcess(DeleteProcess(self, path, items))

  def customEvent(self,event):
    """Handle events from processes"""
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
    
  def getItems(self, path):
    """Returns a list of processable items under the given path"""
    items = []
    for root, dirs, files in os.walk(unicode(path)):
      items.append(root)
      items += [os.path.join(root, f) for f in files if not f.startswith(".")]
    return items

  def getQString(self, qstring):
    """@returns a python string representation of the given QString"""
    return unicode(qstring).encode("latin-1", "replace")
    
  def tr(self, identifier, context = None):
    """Overridden translation method that returns native Python strings"""
    return self.getQString(QObject.tr(self, identifier, context))

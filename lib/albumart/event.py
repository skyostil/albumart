#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from qt import *
import traceback
import sys

class CoverDownloadedEvent(QCustomEvent):
  id = QEvent.User
  def __init__(self, thread, cover):
    QCustomEvent.__init__(self, self.id)
    self.cover = cover
    self.thread = thread

class TaskFinishedEvent(QCustomEvent):
  id = QEvent.User + 1
  def __init__(self, thread, message = None, result = True):
    QCustomEvent.__init__(self, self.id)
    self.thread = thread
    self.message = message
    self.result = result

class ExceptionEvent(QCustomEvent):
  id = QEvent.User + 2
  def __init__(self, thread, x):
    QCustomEvent.__init__(self, self.id)
    self.thread = thread
    self.exception = x
    self.description = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)

class ProgressEvent(QCustomEvent):
  id = QEvent.User + 3
  def __init__(self, thread, progress, total):
    QCustomEvent.__init__(self, self.id)
    self.thread = thread
    self.progress = progress
    self.total = total

class StatusEvent(QCustomEvent):
  id = QEvent.User + 4
  def __init__(self, thread, text):
    QCustomEvent.__init__(self, self.id)
    self.thread = thread
    self.text = text

class ReloadEvent(QCustomEvent):
  id = QEvent.User + 5
  def __init__(self, thread):
    QCustomEvent.__init__(self, self.id)
    self.thread = thread

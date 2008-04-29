import os
from qt import *

import albumart
import webbrowser
from pixmap import getPixmapForPath, resizePixmap

def fillHorizontalGradient(painter, rect, c1, c2):
  def lerp(a, b, f):
    return a + ((f * ((b - a) << 8)) >> 16)

  w = rect.width()
  h = rect.height()
  for x in range(0, w):
    f = (x << 8) / w
    c = QColor(
      lerp(c1.red(), c2.red(), f),
      lerp(c1.green(), c2.green(), f),
      lerp(c1.blue(), c2.blue(), f))
    painter.fillRect(rect.x() + x, rect.y(), 1, h, QBrush(c))

class TrackItem(QListViewItem):
  """A track list item"""
  def __init__(self, album, path):
    QListViewItem.__init__(self, album)
    self.setDropEnabled(True)
    self.path = path
    self.name = os.path.basename(path)
    self.margin = 8
    self.album = album
    self.setText(0, self.name)

  def paintCell(self, painter, colorGroup, column, width, alignment):
    if not self.pixmap(0):
      self.refresh()

    if self.isSelected():
      c1 = colorGroup.highlight().light(110)
      c2 = QColor(255, 255, 255)
      fillHorizontalGradient(painter, QRect(0, 0, width, self.height()), c1, c2)
    else:
      painter.eraseRect(0, 0, width, self.height())

    m = self.listView().itemMargin()
    painter.drawPixmap(m, 0, self.pixmap(0))
    painter.drawText(2 * m + self.pixmap(0).width(), m,
                     width, self.height(), Qt.AlignVCenter, self.name)

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

  def getAlbumName(self):
    """@returns the album name"""
    return self.album.getAlbumName()

  def getArtistName(self):
    """@returns the artist name"""
    return self.album.getArtistName()

  def getPath(self):
    """@returns the path for this item"""
    return self.path

class AlbumItem(QListViewItem):
  """An album list item"""
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
    self.setText(0, self.album)

  def acceptDrops(self, mimeSource):
    return True

  def refresh(self):
    self.setPixmap(0, resizePixmap(getPixmapForPath(self.path), self.iconSize))

  def paintCell(self, painter, colorGroup, column, width, alignment):
    if not self.pixmap(0):
      self.refresh()

    if self.isSelected():
      c1 = colorGroup.highlight().light(110)
      c2 = QColor(255, 255, 255)
      fillHorizontalGradient(painter, QRect(0, 0, width, self.height()), c1, c2)
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
    if self.isSelected():
      painter.setPen(colorGroup.highlight().dark())
      painter.setBrush(colorGroup.highlight().dark())
    else:
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
    if self.pixmap(0):
      return self.pixmap(0).width() + QFontMetrics(self.titleFont).width(self.album) + 16
    return 0

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

  def getAlbumName(self):
    """@returns the album name"""
    return self.album

  def getArtistName(self):
    """@returns the artist name"""
    return self.artist

  def addTrack(self, fileName):
    """Add a new track to this album"""
    if not fileName in self.tracks:
      self.tracks.append(fileName)
    return TrackItem(self, fileName)

  def getTrackCount(self):
    """@returns the number of tracks under this album"""
    return len(self.tracks)

  def getPath(self):
    """@returns the path for this item"""
    return self.path

FileItem = TrackItem

class FolderItem(QListViewItem):
  """A folder item that directly corresponds to a filesystem directory"""
  def __init__(self, parent, path, extensions):
    QListViewItem.__init__(self, parent)
    self.setDropEnabled(True)
    self.path = path
    self.artist, self.album = albumart.guessArtistAndAlbum(path)
    self.tracks = []
    self.margin = 8
    self.iconSize = 64
    self.openTrigger = QRect()
    self.titleFont = QFont(QFont().family(), QFont().pointSize() + 3, QFont.Bold)
    self.setText(0, os.path.basename(self.path))
    self.extensions = extensions
    self.itemCount = len(self.getChildren())

  def acceptDrops(self, mimeSource):
    return True

  def refresh(self):
    self.setPixmap(0, resizePixmap(getPixmapForPath(self.path), self.iconSize))

  def paintCell(self, painter, colorGroup, column, width, alignment):
    if not self.pixmap(0):
      self.refresh()

    if self.isSelected():
      c1 = colorGroup.highlight().light(110)
      c2 = QColor(255, 255, 255)
      fillHorizontalGradient(painter, QRect(0, 0, width, self.height()), c1, c2)
    else:
      painter.eraseRect(0, 0, width, self.height())

    # draw the icon
    m = self.listView().itemMargin()
    painter.drawPixmap(m + self.margin, m + self.margin, self.pixmap(0))
    m += 4

    left = self.pixmap(0).width() + m + self.margin
    painter.setPen(colorGroup.text())
    fontSize = painter.font().pointSize()

    # draw the folder name
    painter.setFont(self.titleFont)
    painter.drawText(left, m + self.margin,
                     width, self.height(), 0, self.text(0))
    titleRect = painter.boundingRect(0, 0, width, self.height(), 0, self.text(0))

    # draw the open indicator
    if self.isSelected():
      painter.setPen(colorGroup.highlight().dark())
      painter.setBrush(colorGroup.highlight().dark())
    else:
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
    self.openTrigger.setRect(left, m + self.margin + titleRect.height() + m + titleRect.height(),
                             smallFontSize, smallFontSize)
    painter.translate(self.openTrigger.left(), self.openTrigger.top())
    painter.drawPolygon(arrow)

    # draw the item count
    painter.setFont(QFont(painter.font().family(), smallFontSize))
    text = str(self.itemCount) + (self.itemCount == 1 and " item" or " items")
    painter.drawText(self.openTrigger.width() + m, 0,
                     width, self.height() / 2, 0, text)

  def paintFocus(self, painter, colorGroup, rect):
    pass

  def paintBranches(self, painter, colorGroup, w, y, h, style = None):
    painter.eraseRect(0, 0, w, h)

  def width(self, fontMetrics, listView, column):
    if self.pixmap(0):
      return self.pixmap(0).width() + QFontMetrics(self.titleFont).width(self.text(0)) + 16
    return 0

  def setup(self):
    self.setHeight(self.iconSize + self.margin * 2)

  def getChildren(self):
    try:
      return [os.path.join(self.path, fn) for fn in os.listdir(self.path) \
              if (os.path.isdir(os.path.join(self.path, fn)) or \
                  os.path.splitext(fn)[1].lower()[1:] in self.extensions) and \
                not fn.startswith(".")]
    except:
      return []

  def activate(self):
    # read our contents if it hasn't been done before
    if self.childCount() == 0:
      for fileName in self.getChildren():
        if os.path.isdir(fileName):
          FolderItem(self, fileName, self.extensions)
        elif os.path.isfile(fileName):
          FileItem(self, fileName)

    # open the album if the cursor is within the trigger
    p = self.listView().mapFromGlobal(QCursor.pos())
    p.setY(p.y() - self.itemPos() + self.listView().contentsY())
    if p.y() >= self.openTrigger.top() and \
       p.x() > self.openTrigger.left() - 4 and \
       p.x() < self.openTrigger.right() + 4:
      self.setOpen(not self.isOpen())

  def getAlbumName(self):
    """@returns the album name"""
    return self.album

  def getArtistName(self):
    """@returns the artist name"""
    return self.artist

  def addTrack(self, fileName):
    """Add a new track to this album"""
    if not fileName in self.tracks:
      self.tracks.append(fileName)
    return TrackItem(self, fileName)

  def getTrackCount(self):
    """@returns the number of tracks under this album"""
    return len(self.tracks)

  def getPath(self):
    """@returns the path for this item"""
    return self.path

class CoverItem(QIconViewItem):
  """A cover image item"""
  def __init__(self, parent, pixmap, path, delete = False, text = None, linkUrl = None, linkText = None):
    QListViewItem.__init__(self, parent, "", pixmap)
    self.margin = 6
    self.path = path
    self.text = text
    self.linkUrl = linkUrl
    self.linkText = linkText
    self.delete = delete
    self.fontHeight = self.iconView().fontInfo().pixelSize() + 2
    lines = self.linkUrl and 2 or 1
    self.setItemRect(QRect(0, 0,
                           self.pixmap().width() + self.margin * 2,
                           self.pixmap().height() + self.margin * 2 + self.fontHeight * lines))

  def __del__(self):
    # delete the temporary file if needed
    try:
      if self.delete:
        os.unlink(self.path)
    except:
      pass

  def getPath(self):
    """@returns the path for this item"""
    return self.path

  def paintFocus(self, painter, colorGroup):
    pass

  def onClicked(self, itemPos):
    if self.linkUrl and itemPos.y() >= self.height() - self.fontHeight:
      print "Browsing to", self.linkUrl
      webbrowser.open(self.linkUrl)

  def paintItem(self, painter, colorGroup):
    if self.isSelected():
      painter.setBrush(colorGroup.highlight().light(120))
      painter.setPen(colorGroup.dark())
      painter.drawRoundRect(self.x(), self.y(),
                            self.width(), self.height(),
                            self.margin, self.margin)

    painter.drawPixmap(self.x() + self.margin,
                       self.y() + self.margin, self.pixmap())
    if self.text:
      r = QRect(self.x() + self.margin,
                self.y() + self.margin + self.pixmap().height(),
                self.pixmap().width(), self.fontHeight)
      painter.drawText(r, Qt.AlignCenter, self.text)

    if self.linkText:
      r = QRect(self.x() + self.margin,
                self.y() + self.margin + self.pixmap().height() + self.fontHeight,
                self.pixmap().width(), self.fontHeight)
      f = QFont(self.iconView().font())
      f.setUnderline(True)
      painter.setPen(colorGroup.link())
      painter.setFont(f)
      painter.drawText(r, Qt.AlignCenter, self.linkText)

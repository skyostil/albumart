from qt import *

import albumart
import albumart_images

# empty cover pixmap
noCoverPixmap = None

def getPixmapForPath(path):
  """@returns a QPixmap representing the given path"""
  def loadPixmap(name):
    pixmap = QPixmap()
    img = QImage()
    QImageDrag.decode(albumart_images.MimeSourceFactory_albumart().data(QString(name)), img)
    pixmap.convertFromImage(img)
    return pixmap
  
  global noCoverPixmap
  
  if not noCoverPixmap:
    noCoverPixmap = loadPixmap("nocover.png")

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

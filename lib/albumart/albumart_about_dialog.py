from albumart_about_dialog_base import AboutDialogBase
from qt import *
import version

import webbrowser

class AboutDialog(AboutDialogBase):
  def __init__(self, parent):
    AboutDialogBase.__init__(self, parent)
    self.version.setText("<h2>%s</h2><p>Version %s</p>" % (version.__program__, version.__version__))
    self.urlButton.setText(version.__url__)
    self.creditsEdit.setText("""<p>Copyright &copy; 2003-2005 by <b>%(author)s</b></p>
<p>Amazon web api wrapper by <b>Mark Pilgrim</b> and <b>Michael Josephson</b> (http://www.josephson.org/projects/pyamazon/)</p>
<p>Icons by <b>Everaldo Coelho</b> (http://www.everaldo.com) et al from the KDE project (http://www.kde.org)</p>
<p>PyID3 by <b>Myers Carpenter</b> (http://icepick.info/projects/pyid3/)</p>
""" % \
    {
      "author" : version.__author__
    })

  def openHomePage(self):
    webbrowser.open_new(version.__url__)

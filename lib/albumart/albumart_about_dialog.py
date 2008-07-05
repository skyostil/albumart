from albumart_about_dialog_base import AboutDialogBase
from qt import *
import version

import webbrowser

class AboutDialog(AboutDialogBase):
  def __init__(self, parent):
    AboutDialogBase.__init__(self, parent)
    self.version.setText("<h2>%s</h2><p>Version %s</p>" % (version.__program__, version.__version__))
    self.urlButton.setText(version.__url__)
    self.creditsEdit.setText("""<p>Copyright &copy; 2003-2008 by <b>%(author)s</b></p>
<p>Amazon web api wrapper by <b>Mark Pilgrim</b> and <b>Michael Josephson</b> (http://www.josephson.org/projects/pyamazon/)</p>
<p>Icons by <b>Everaldo Coelho</b> (http://www.everaldo.com) et al from the KDE project (http://www.kde.org)</p>
<p>PyID3 by <b>Myers Carpenter</b> (http://icepick.info/projects/pyid3/)</p>
<p>Walmart image source based on code by by <b>Filip Kalinski</b></p>
<p>
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
</p><p>
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
</p><p>
    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
</p>
""" % \
    {
      "author" : version.__author__
    })

  def openHomePage(self):
    webbrowser.open_new(version.__url__)

from qt import *
from albumart_exception_dialog_base import ExceptionDialogBase

class ExceptionDialog(ExceptionDialogBase):
  def __init__(self, parent, task, description):
    ExceptionDialogBase.__init__(self, parent)
    self.message.setText(self.tr((
            "<p>%(task)s was interrupted by the following exception:</p><p>%(description)s</p>") % \
            {"task" : task, "description": description[-1]}))
    self.traceback.hide()
    self.traceback.setText("<pre>" + "\n".join(description) + "</pre>")

  def showTraceback(self):
    self.traceback.show()
    self.resize(700, 425)
    self.pushMore.setEnabled(False)

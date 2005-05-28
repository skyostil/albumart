from albumart_string_list_widget_base import StringListWidgetBase
from qt import *

class StringListWidget(StringListWidgetBase):
  """A user editable list of strings"""
  def __init__(self, parent, name, items):
    StringListWidgetBase.__init__(self, parent, name)
    for item in items:
      self.listBox.insertItem(item)

  def textChanged(self):
    self.addButton.setEnabled(str(self.lineEdit.text()) and True or False)

  def addButtonClicked(self):
    self.listBox.insertItem(self.lineEdit.text())
    self.lineEdit.setText("")

  def removeButtonClicked(self):
    self.listBox.removeItem(self.listBox.currentItem())
    self.removeButton.setEnabled(False)

  def itemSelected(self):
    self.lineEdit.setText(self.listBox.currentText())
    self.removeButton.setEnabled(True)

  def getItems(self):
    items = []
    for i in range(0, self.listBox.count()):
      items.append(str(self.listBox.text(i)))
    return items
    
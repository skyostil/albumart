from albumart_configuration_dialog_base import ConfigurationDialogBase
from albumart_string_list_widget import StringListWidget
from qt import *
import albumart
import version

class ConfigurationDialog(ConfigurationDialogBase):
  """A configuration dialog"""
  def __init__(self, parent, modules):
    ConfigurationDialogBase.__init__(self, parent)
    self.version.setText("<h2>%s</h2><p>Version %s</p>" % (version.__program__, version.__version__))
    self.modules = modules
    self.widgets = {}
    self.categories = {
      albumart.Source: QListViewItem(self.pageView, "Sources"),
      albumart.Target: QListViewItem(self.pageView, "Targets"),
      albumart.Recognizer: QListViewItem(self.pageView, "Recognizers")
    }
    self.pages = {}

    for m in modules:
      self.addModule(m)

    # open all categories
    for c in self.categories.values():
      c.setOpen(True)

  def getCategoryItem(self, module):
    for c, i in self.categories.items():
      if isinstance(module, c):
        return i
    return self.pageView

  def createConfigurationWidgets(self, module, parent, layout, configDesc):
    config = module.__configuration__
    self.widgets[module] = []
    for key, desc in configDesc.items():
      if len(desc) == 1:
        continue
      labelText = desc[1] + ((desc[1][0] == "<") and " " or ":")
      if desc[0] == "boolean":
        k = w = QCheckBox(desc[1], parent, key)
        w.setChecked(config[key])
      elif desc[0] == "string":
        f = QWidget(parent)
        l = QHBoxLayout(f)
        w = QLabel(labelText, f)
        l.addWidget(w)
        k = w = QLineEdit(config[key], f, key)
        l.addWidget(w)
        w = f
      elif desc[0] == "choice":
        f = QWidget(parent)
        l = QHBoxLayout(f)
        w = QLabel(labelText, f)
        l.addWidget(w)
        k = w = QComboBox(False, f, key)
        items = desc[2]
        items.sort()
        for s in items:
          w.insertItem(s)
        w.setCurrentText(config[key])
        l.addWidget(w)
        w = f
      elif desc[0] == "integer":
        f = QWidget(parent)
        l = QHBoxLayout(f)
        w = QLabel(labelText, f)
        l.addWidget(w)
        k = w = QSpinBox(desc[2][0], desc[2][1], 1, f, key)
        w.setValue(int(config[key]))
        l.addWidget(w)
        w = f
      elif desc[0] == "stringlist":
        f = QWidget(parent)
        l = QHBoxLayout(f)
        w = QLabel(labelText, f)
        l.addWidget(w)
        k = w = StringListWidget(f, key, config[key])
        l.addWidget(w)
        w = f
      else:
        continue
      self.widgets[module].append(k)
      # make sure the enable toggles are at the top
      if key == "enabled":
        layout.insertWidget(3, w)
      else:
        layout.addWidget(w)

  def addModule(self, module):
    m = __import__(module.__module__)
    configDesc = m.configDesc

    if configDesc:
      page = QWidget(self)
      layout = QVBoxLayout(page)
      layout.setSpacing(8)
      layout.setMargin(8)

      title = QLabel("<h1>%s</h1>" % module.__doc__, page)
      layout.addWidget(title)
      desc = QLabel("<p>%s</p>" % m.__doc__, page)
      layout.addWidget(desc)
      frame = QFrame(page)
      frame.setFrameShape(QFrame.HLine)
      frame.setFrameShadow(QFrame.Sunken)
      layout.addWidget(frame)

      self.createConfigurationWidgets(module, page, layout, configDesc)
      layout.addStretch()

      page.show()
      n = self.pageStack.addWidget(page)
      self.pages[QListViewItem(self.getCategoryItem(module), module.__doc__)] = n

  def accept(self):
    for module, widgets in self.widgets.items():
      for widget in widgets:
        cfg = module.__configuration__
        if isinstance(widget, QCheckBox):
          cfg[widget.name()] = widget.isChecked() and 1 or 0
        elif isinstance(widget, QLineEdit):
          cfg[widget.name()] = str(widget.text())
        elif isinstance(widget, QComboBox):
          cfg[widget.name()] = str(widget.currentText())
        elif isinstance(widget, QSpinBox):
          cfg[widget.name()] = widget.value()
        elif isinstance(widget, StringListWidget):
          cfg[widget.name()] = widget.getItems()
      module.configure(module.__configuration__)
    ConfigurationDialogBase.accept(self)

  def setPage(self, page):
    try:
      self.pageStack.raiseWidget(self.pages[page])
    except KeyError:
      pass

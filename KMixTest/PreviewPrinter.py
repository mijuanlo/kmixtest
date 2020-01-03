from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Util import print_document_data, print_preview_data, print_printer_data

# class for pdf preview object
class previewPrinter(QPrintPreviewDialog):
    toolbar = None
    actions = None

    def __init__(self, parent=None, printer=None):
        if parent is not None:
            self.parent = parent
        super().__init__(printer)
        self.preview = self.findChild(QPrintPreviewWidget)
        #self.toolbar = self.findChild(QToolBar)
        #self.actions = { a.iconText() : a for a in self.toolbar.actions() if (type(a) == type(QAction()) and a.isVisible()) and not a.isSeparator() }
        self.setupButtons()
    
    def setupButtons(self):
        self.preview.previewChanged.connect(self.previewChanged)

    @Slot()
    def previewChanged(self):
        qDebug("***** Preview changed! *****")
        print_preview_data(self.preview)
        print_printer_data(self.parent.printer)

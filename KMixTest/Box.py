from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Config import ICONS

# Custom object for display content questions
class Box(QGroupBox):
    closedBox = Signal(str)
    button_space = 4
    button_size = 22

    def __init__(self,title=None,parent=None):
        self.id = str(id(self))
        super().__init__(title="{}-{}".format(title,self.id[-6:]),parent=parent)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        self.button = QPushButton(QIcon(ICONS['close']),"",self)
        self.button.setFlat(True)
        self.button.setStyleSheet('border: none')
        self.button.setIconSize(QSize(self.button_size,self.button_size))
        self.button.resize(self.button_size,self.button_size)
        self.button.move(self.width()-self.button.width()-self.button_space,self.button_space)
        self.button.clicked.connect(self.closeBox)

    def getId(self):
        return self.id

    def getGrid(self):
        return self.layout

    def resizeEvent(self, event):
        self.button.move(self.width()-self.button.width()-self.button_space,self.button_space)
        super().resizeEvent(event)
    
    def addTo(self, on):
        on.addWidget(self)
        return self,self.layout

    Slot()
    def closeBox(self):
        self.closedBox.emit(self.id)

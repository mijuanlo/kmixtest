from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .MenuItem import MenuItem
from .Config import ICONS

# Custom object for display content questions
class Box(QGroupBox):
    closedBox = Signal(str)
    button_space = 4
    button_size = 22

    contentChanged = Signal(str,str)

    def __init__(self,title=None,parent=None):
        self.id = str(id(self))
        # super().__init__(title="{}-{}".format(title,self.id[-6:]),parent=parent)
        super().__init__(title=" ",parent=parent)
        self.menu = MenuItem(menu=QToolBar(self),parent=self)
        self.menu.addMenuItem(["Add option|add","Remove option|remove"])
        #self.menu.menu.setStyleSheet("QToolButton#add_option { background-color: white; }")
        
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        self.button = QPushButton(QIcon(ICONS['close']),"",self)
        self.button.setFlat(True)
        #self.button.setStyleSheet('border: none')
        self.button.setIconSize(QSize(self.button_size,self.button_size))
        self.button.resize(self.button_size,self.button_size)
        self.button.move(self.width()-self.button.width()-self.button_space,self.button_space)
        self.button.clicked.connect(self.closeBox)
        self.data = None
        self.datadict = {}
        self.editableItems = {}

    def setData(self,key=None,value=None):
        if key is not None and value is None:
            self.data = key
        if key is not None and value is not None:
            self.data = {}
            self.data[key] = value

    def getData(self,key=None):
        if key is None:
            return self.data
        else:
            return self.datadict.get(key,None)

    def getId(self):
        return self.id

    def getGrid(self):
        return self.layout

    def resizeEvent(self, event):
        self.button.move(self.width()-self.button.width()-self.button_space,self.button_space)
        super().resizeEvent(event)

    Slot()
    def closeBox(self):
        self.closedBox.emit(self.id)

    def addTitleEditor(self, content=None ):
        label = QLabel("Title")
        if content:
            textedit = QTextEdit(content)
        else:
            textedit = QTextEdit()
        textedit.textChanged.connect(self.titleEditorChanged)
        self.editableItems.setdefault('TITLE_EDITOR',textedit)
        self.layout.addWidget(label,0,0)
        self.layout.addWidget(textedit,0,1)

    @Slot()
    def titleEditorChanged(self):
        self.contentChanged.emit(self.id,self.editableItems.get('TITLE_EDITOR').toPlainText())
    
    def updateTitle(self,content):
        textedit = self.editableItems.get('TITLE_EDITOR')
        if textedit and content and isinstance(content,str) :
            textedit.setText(content)

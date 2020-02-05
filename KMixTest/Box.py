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
    button_space = 6
    button_size = 36
    column_width = 60

    contentChanged = Signal(str,str)

    def __init__(self,parent=None):
        self.id = str(id(self))
        super().__init__(parent=parent)
        self.layout = QGridLayout(self)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)
        self.setLayout(self.layout)
        self.toolbar = QToolBar(self)
        self.toolbar.setFixedHeight(self.button_size)
        self.addToLayout(self.toolbar,True)
        # self.separator = QFrame(self)
        # self.separator.setFrameShape(QFrame.HLine)
        # self.separator.setFrameShadow(QFrame.Sunken)
        # self.addToLayout(self.separator,True)
        self.menu = MenuItem(menu=self.toolbar,parent=self)
        #self.toolbar.setStyleSheet('QToolBar { padding-bottom : 0px; }')
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

    def addToLayout(self,items,span=False):
        current_row = self.layout.rowCount()
        current_col = 0
        if not isinstance(items,list):
            self.addToLayout([items],span)
        else:
            for i in items:
                align = Qt.Alignment()
                if isinstance(i,tuple):
                    i,align = i
                rowspan = 1
                colspan = 1
                if span:
                    colspan = -1
                if isinstance(i,QWidget):
                    self.layout.addWidget(i,current_row,current_col,rowspan,colspan,align)
                elif isinstance(i,QLayoutItem):
                    self.layout.addItem(i,current_row,current_col,rowspan,colspan,align)
                else:
                    raise ValueError()
                current_col += 1

    def setData(self,key=None,value=None):
        if key is not None and value is None:
            if isinstance(self.data,dict):
                raise ValueError()
            self.data = key
        if key is not None and value is not None:
            if not (self.data is None or isinstance(self.data,dict)):
                raise ValueError()
            if self.data is None:
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
        label.setFixedWidth(self.column_width)
        label.setStyleSheet('QLabel {{ margin-top: {}px; }}'.format(self.button_size))
        if content:
            textedit = QTextEdit(content)
        else:
            textedit = QTextEdit()
        textedit.textChanged.connect(self.titleEditorChanged)
        self.editableItems.setdefault('TITLE_EDITOR',textedit)
        self.addToLayout([(label,Qt.AlignTop|Qt.AlignHCenter),textedit])
        #self.addToLayout(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Expanding))

    def addTestEditor(self,content=None):
        self.addTitleEditor(content)
        pass

    @Slot()
    def titleEditorChanged(self):
        self.contentChanged.emit(self.id,self.editableItems.get('TITLE_EDITOR').toPlainText())

    def updateTitle(self,content):
        textedit = self.editableItems.get('TITLE_EDITOR')
        if textedit and content and isinstance(content,str) :
            textedit.setText(content)

    def makeQuestionTypeLayout(self):
        typeQuestion = self.data.get('type')
        if not typeQuestion:
            qDebug('Empty type for question received')
        if typeQuestion == 'single_question':
            self.menu.emptyMenu()
            self.addToLayout(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Fixed))
            #self.menu.addMenuItem(["Add option|add","Remove option|remove"])
            self.addTitleEditor(self.data.get('initial_content'))
        elif typeQuestion == 'test_question':
            self.menu.emptyMenu()
            self.menu.addMenuItem(["Add option(test_question_add)|add","Remove option(test_question_remove)|remove"])
            self.addTestEditor(self.data.get('initial_content'))
            pass
        elif typeQuestion == 'join_activity':
            self.menu.emptyMenu()
            pass
        else:
            qDebug('type for question "{}" unknown, skipping'.format(typeQuestion))

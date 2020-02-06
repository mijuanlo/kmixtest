from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .MenuItem import MenuItem
from .QPushButtonTest import QPushButtonTest
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
        self.lock = False

    def addToLayout(self,items,span=False):
        current_row = self.layout.rowCount()
        current_col = 0
        if not isinstance(items,list):
            self.addToLayout([items],span)
        else:
            for i in items:
                align = Qt.Alignment()
                if isinstance(i,tuple):
                    if len(i) == 2:
                        i,align = i
                    elif len(i) == 3:
                        i,align,span = i
                        if not align:
                            align = Qt.Alignment()
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
        self.addToLayout([(label,Qt.AlignTop|Qt.AlignHCenter),(textedit,'',True)])
        #self.addToLayout(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Expanding))

    def addTestEditor(self,content=None):
        self.addTitleEditor(content)
        self.optionController = QButtonGroup(self)
        self.optionController.setExclusive(True)
    
    def addOptionToTest(self):
        number = self.data.get('number_of_options')
        if not number:
            number = 1
            self.data.setdefault('number_of_options',number)
        else:
            number += 1
            self.data['number_of_options'] = number
        #label = QLabel("Option#{}".format(number))
        label = QLabel("Option")
        label.setFixedWidth(self.column_width)
        lineEdit = QLineEdit()
        button_ok = QPushButtonTest("",parent=self)
        button_ok.setFixedHeight(self.button_size)
        button_ok.setFixedWidth(self.button_size)
        button_remove = QPushButton(QIcon(ICONS['remove']),"",self)
        button_remove.clicked.connect(lambda: self.removeClicked(number))
        button_remove.setFixedHeight(self.button_size)
        button_remove.setFixedWidth(self.button_size)
        button_remove.setStyleSheet('border:0px;')
        self.editableItems.setdefault('OptionLineEdit#{}'.format(number),lineEdit)
        self.editableItems.setdefault('OptionButtonOk#{}'.format(number),button_ok)
        self.editableItems.setdefault('OptionButtonRemove#{}'.format(number),button_remove)
        self.optionController.addButton(button_ok,number)
        self.addToLayout([(label,Qt.AlignCenter),lineEdit,button_ok,button_remove])
    
    def removeClicked(self,number):
        qDebug('removeClicked from {}'.format(number))
        if self.optionController.checkedId() == number:
            for b in self.optionController.buttons():
                if b._id != number:
                    b.reset()
        self.removeOptionFromTest(number)

    def findItemLayoutRow(self,widget):
        for y in range(self.layout.rowCount()):
            for x in range(self.layout.columnCount()):
                widgetitem = self.layout.itemAtPosition(y,x)
                if widgetitem and widgetitem.widget() is widget:
                    return y
        return None

    def removeRowItems(self,row):
        for x in range(self.layout.columnCount()):
            widgetitem = self.layout.itemAtPosition(row,x)
            if widgetitem:
                widget = widgetitem.widget()
                if widget:
                    self.removeWidget(widget)
                del widgetitem

    def removeWidget(self,widget):
        if not isinstance(widget,list):
            widget = [ widget ]
        toRemove = list()
        for i in widget:
            for k,v in self.editableItems.items():
                if v is i:
                    toRemove.append(k)
                    break
            i.deleteLater()
        for w in toRemove:
            del self.editableItems[w]

    def removeOptionFromTest(self,number=None):
        if not number:
            options = [ x.split('#')[1] for x in self.editableItems.keys() if 'OptionLineEdit#' in x ]
            if options:
                options = sorted(options)
                if options:
                    number = options.pop()
        if number:
            lineedit = self.editableItems.get('OptionLineEdit#{}'.format(number))
            if lineedit:
                row = self.findItemLayoutRow(lineedit)
                self.removeRowItems(row)

    @Slot()
    def titleEditorChanged(self):
        self.contentChanged.emit(self.id,self.editableItems.get('TITLE_EDITOR').toPlainText())

    def updateTitle(self,content):
        textedit = self.editableItems.get('TITLE_EDITOR')
        if textedit and content and isinstance(content,str):
            textedit.setText(content)

    @Slot(str)
    def controllerQuestions(self,*args,**kwargs):
        qDebug('Called controllerQuestions')
        if not args:
            if self.sender():
                data = self.sender().data()
            else:
                raise ValueError()
        else:
            data = args[0]
        if not data:
            raise ValueError()
        qDebug('controllerQuestions "{}" click'.format(data))
        if data == 'test_question_add':
            if not self.lock:
                self.addOptionToTest()
        elif data == 'test_question_remove':
            if not self.lock:
                self.removeOptionFromTest()
        elif data == 'box_lock':
            self.lock = True
            self.do_lock()
        elif data == 'box_unlock':
            self.lock = False
            self.do_lock()
        else:
             qDebug("No action declared for '{}' controllerQuestions".format(data))

    def do_lock(self):
        if self.lock:
            for k,v in self.editableItems.items():
                if isinstance(v,QAbstractButton):
                    v.setDisabled(True)
                else:
                    v.setReadOnly(True)
            buttons = self.menu.getButtons()
            for name,b in buttons.items():
                if name == 'unlock':
                    b.setEnabled(True)
                else:
                    b.setDisabled(True)
        else:
            for k,v in self.editableItems.items():
                if isinstance(v,QAbstractButton):
                    v.setDisabled(False)
                else:
                    v.setReadOnly(False)
            buttons = self.menu.getButtons() 
            for name,b in buttons.items():
                if name == 'unlock':
                    b.setDisabled(True)
                else:
                    b.setEnabled(True)

    def makeQuestionTypeLayout(self):
        typeQuestion = self.data.get('type')
        if not typeQuestion:
            qDebug('Empty type for question received')
        if typeQuestion == 'single_question':
            self.menu.emptyMenu()
            self.menu.addMenuItem(["Lock(box_lock)|lock","Unlock(box_unlock)|unlock"])
            self.addToLayout(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Fixed))
            #self.menu.addMenuItem(["Add option|add","Remove option|remove"])
            self.addTitleEditor(self.data.get('initial_content'))
            self.do_lock()
        elif typeQuestion == 'test_question':
            self.menu.emptyMenu()
            self.menu.addMenuItem(["Add option(test_question_add)|add","Remove option(test_question_remove)|remove","Lock(box_lock)|lock","Unlock(box_unlock)|unlock"])
            self.menu.itemActivation.connect(self.controllerQuestions)
            self.addTestEditor(self.data.get('initial_content'))
            self.do_lock()
        elif typeQuestion == 'join_activity':
            self.menu.emptyMenu()
            self.do_lock()
            pass
        else:
            qDebug('type for question "{}" unknown, skipping'.format(typeQuestion))

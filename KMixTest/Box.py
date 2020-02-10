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
    button_size = 28
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
        self.count_trues = 0
        self.options_declared = {}
        self.pushed_order = []
        self.empty_lines_for_answer = 0

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

    @Slot()
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

    def addOptionToTest(self):
        number = self.data.get('number_of_options')
        if not number:
            number = 1
            self.data.setdefault('number_of_options',number)
        else:
            number += 1
            self.data['number_of_options'] = number
        label = QLabel("Option")
        label.setFixedWidth(self.column_width)
        lineEdit = QLineEdit()
        name_button_ok = "ValueButtonOk#{}".format(number)
        name_button_remove = 'ValueButtonRemove#{}'.format(number)
        button_ok = QPushButtonTest("",name=name_button_ok,parent=self)
        button_ok.clicked.connect(self.buttonsChanged)
        button_ok.setFixedHeight(self.button_size)
        button_ok.setFixedWidth(self.button_size)
        button_remove = QPushButton(QIcon(ICONS['remove']),"",self)
        button_remove.setObjectName(name_button_remove)
        button_remove.clicked.connect(self.removeClicked)
        button_remove.setFixedHeight(self.button_size)
        button_remove.setFixedWidth(self.button_size)
        button_remove.setStyleSheet('border:0px;')
        option_name = 'OptionLineEdit#{}'.format(number)
        self.editableItems.setdefault(option_name,lineEdit)
        self.options_declared.setdefault(str(number),{'text': '', 'trueness': None })
        lineEdit.textChanged.connect(self.optionsChanged)
        self.editableItems.setdefault('OptionButtonOk#{}'.format(number),button_ok)
        self.editableItems.setdefault('OptionButtonRemove#{}'.format(number),button_remove)
        self.addToLayout([(label,Qt.AlignCenter),lineEdit,button_ok,button_remove])

    def getNumber(self,name):
        return name.split('#')[1]

    @Slot(int)
    def buttonsChanged(self,checked=None):
        sender = self.sender()
        if sender:
            name = sender.objectName()
        else:
            name = None
        if name:
            if checked is not None:
                num = self.getNumber(name)

        default = None
        only_repaint = checked is None
        
        if not only_repaint and self.options_declared[num]['trueness']:
            self.options_declared[num]['trueness'] = default
        else:
            num_ok = len([ x for x in self.options_declared if self.options_declared[x]['trueness'] == True])
            if only_repaint:
                if num_ok == self.count_trues:
                    default = False
            else:
                if num_ok == self.count_trues -1:
                    default = False
                elif num_ok == self.count_trues:
                    return

            if not only_repaint:
                state = self.options_declared[num]['trueness']
                if state:
                    state = default
                else:
                    state = True
                self.options_declared[num]['trueness'] = state

        for num in self.options_declared:
            if self.options_declared[num]['trueness']:
                self.editableItems['OptionButtonOk#{}'.format(num)].changeIcon(True)
            else:
                self.editableItems['OptionButtonOk#{}'.format(num)].changeIcon(default)

    @Slot(str)
    def optionsChanged(self,text):
        options = self.getCurrentOptions()
        for name,value in options.items():
            self.options_declared[self.getNumber(name)]['text'] = value.text()

    def getOptionButtons(self):
        return { k:v for k,v in self.editableItems.items() if 'OptionButtonOk#' in k }

    @Slot(int)
    def removeClicked(self,checked=None):
        sender = self.sender()
        if not sender:
            raise ValueError()
        number = self.getNumber(sender.objectName())
        qDebug('removeClicked from {}'.format(number))
        self.removeOptionFromTest(number)
        self.buttonsChanged()

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

    def getCurrentOptions(self):
        return { k:v for k,v in self.editableItems.items() if 'OptionLineEdit#' in k }

    def removeOptionFromTest(self,number=None):
        if not number:
            options = [ self.getNumber(x) for x in self.getCurrentOptions().keys() ]
            if options:
                options = sorted(options)
                if options:
                    number = options.pop()
        if number:
            lineedit = self.editableItems.get('OptionLineEdit#{}'.format(number))
            if lineedit:
                row = self.findItemLayoutRow(lineedit)
                self.removeRowItems(row)
                del self.options_declared[str(number)]

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
                opt = self.getCurrentOptions()
                self.configureSlider(min=1,max=len(opt))
        elif data == 'test_question_remove':
            if not self.lock:
                self.removeOptionFromTest()
                opt = self.getCurrentOptions()
                self.configureSlider(min=1,max=len(opt))
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
                if isinstance(v,(QAbstractButton,QAbstractSlider)):
                    v.setDisabled(True)
                elif isinstance(v,(QLineEdit,QTextEdit)):
                    v.setReadOnly(True)
                elif isinstance(v,(QLabel)):
                    pass
                else:
                    raise ValueError("Can't lock {}".format(v))

            buttons = self.menu.getButtons()
            for name,b in buttons.items():
                if name == 'unlock':
                    b.setEnabled(True)
                else:
                    b.setDisabled(True)
        else:
            for k,v in self.editableItems.items():
                if isinstance(v,(QAbstractButton,QAbstractSlider)):
                    v.setDisabled(False)
                elif isinstance(v,(QLineEdit,QTextEdit)):
                    v.setReadOnly(False)
                elif isinstance(v,(QLabel)):
                    pass
                else:
                    raise ValueError("Can't unlock {}".format(v))

            buttons = self.menu.getButtons() 
            for name,b in buttons.items():
                if name == 'unlock':
                    b.setDisabled(True)
                else:
                    b.setEnabled(True)

    def addSlider(self,container,label,callback):
        title = QLabel(label)
        title.setStyleSheet('margin-right: 5px')
        slider = QSlider()
        slider.setOrientation(Qt.Horizontal)
        slider.setFixedWidth(100)
        slider.setMinimum(1)
        slider.setMaximum(1)
        label = QLabel('0/0')
        label.setFont(QFont('Arial',10,QFont.Normal))
        label.setStyleSheet('margin-left: 5px')
        container.addWidget(title)
        container.addWidget(slider)
        container.addWidget(label)
        slider.valueChanged.connect(callback)
        self.editableItems['SLIDER_CONTROL'] = slider
        self.editableItems['SLIDER_LABEL'] = label
        slider.valueChanged.emit(1)

    def updateLinesForAnswer(self,value):
        self.empty_lines_for_answer = value
        self.editableItems['EMPTY_LINES_LABEL'].setText('Empty lines for answer: {}'.format(value))

    @Slot(int)
    def sliderChanged(self, value=None):
        if value is None:
            return
        slider = self.editableItems['SLIDER_CONTROL']
        label = self.editableItems['SLIDER_LABEL']
        label.setText("{}/{}".format(value,slider.maximum()))
        type_question = self.data.get('type')
        if type_question == 'single_question':
            self.updateLinesForAnswer(value)
        elif type_question == 'test_question':
            for x in self.options_declared:
                old_value = self.options_declared[x]['trueness']
                if self.count_trues > value or not old_value:
                    self.options_declared[x]['trueness'] = None
            self.count_trues = value
            self.buttonsChanged()

    def configureSlider(self,min=1,max=1):
        if min and min < 1:
            min = 1
        if max and max < 1:
            max = 1
        slider = self.editableItems.get('SLIDER_CONTROL')
        value = slider.value()
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.setSliderPosition(value)
        slider.valueChanged.emit(slider.value())

    def makeQuestionTypeLayout(self):
        typeQuestion = self.data.get('type')
        if not typeQuestion:
            qDebug('Empty type for question received')
        if typeQuestion == 'single_question':
            self.menu.emptyMenu()
            self.menu.addMenuItem(["Lock(box_lock)|lock","Unlock(box_unlock)|unlock"])
            self.menu.itemActivation.connect(self.controllerQuestions)
            self.addSlider(self.menu.menu,'Empty lines:',self.sliderChanged)
            self.addToLayout(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Fixed))
            self.addTitleEditor(self.data.get('initial_content'))
            self.editableItems['EMPTY_LINES_LABEL'] = QLabel()
            self.addToLayout([(self.editableItems['EMPTY_LINES_LABEL'],Qt.AlignCenter,True)])
            self.configureSlider(1,30)
            self.do_lock()
        elif typeQuestion == 'test_question':
            self.menu.emptyMenu()
            self.menu.addMenuItem(["Add option(test_question_add)|add","Remove option(test_question_remove)|remove","Lock(box_lock)|lock","Unlock(box_unlock)|unlock"])
            self.menu.itemActivation.connect(self.controllerQuestions)
            self.addSlider(self.menu.menu,'Valid:',self.sliderChanged)
            self.addTitleEditor(self.data.get('initial_content'))
            self.do_lock()
        elif typeQuestion == 'join_activity':
            self.menu.emptyMenu()
            self.do_lock()
            pass
        else:
            qDebug('type for question "{}" unknown, skipping'.format(typeQuestion))

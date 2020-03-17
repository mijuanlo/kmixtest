from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .MenuItem import MenuItem
from .QPushButtonTest import QPushButtonTest
from .Config import ICONS
from .QuestionType import Question
from .Util import dumpPixMapData,loadPixMapData

from os.path import expanduser
from copy import deepcopy
from pprint import pformat as pp

import gettext
_ = gettext.gettext

VIEW_DUMP_OPTION = True

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
        self._layout = QGridLayout(self)
        self._layout.setVerticalSpacing(0)
        self._layout.setHorizontalSpacing(0)
        self.setLayout(self._layout)
        self.toolbar = QToolBar(self)
        self.toolbar.setFixedHeight(self.button_size)
        self.addToLayout(self.toolbar,True)
        self.menu = MenuItem(menu=self.toolbar,parent=self)
        self.button = QPushButton(QIcon(ICONS['close']),"",self)
        self.button.setFlat(True)
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

    def layoutInsertAfter(self,widgetWithLayout,widgetBefore,widgetTupleAfter):
        # Gridlayout hasn't insertWidget method that can be used with indexOf(widget)
        layout = widgetWithLayout.layout()
        if not isinstance(layout,QGridLayout):
            raise ValueError()
        new_layout = QGridLayout()
        new_layout.setVerticalSpacing(0)
        new_layout.setHorizontalSpacing(0)
        positions = {}
        after_position = None
        for k in range(layout.count()):
            y,x,yspan,xspan = layout.getItemPosition(0)
            item = layout.takeAt(0)
            widget = item.widget()
            positions.setdefault(y,{})
            if not widget:
                content = {'item': item,'yspan':yspan,'xspan':xspan,'align':item.alignment()}
            else:
                content = {'widget':widget,'yspan':yspan,'xspan':xspan,'align':item.alignment()}
            positions[y].setdefault(x,content)
            if widget is widgetBefore:
                after_position = y
        if not after_position:
            raise ValueError()
        insertOffset = 0
        do_insertion = False
        for y in sorted(positions.keys()):
            for x in sorted(positions[y].keys()):
                content = positions[y][x]
                if 'widget' in content:
                    new_layout.addWidget(content['widget'],y+insertOffset,x,content['yspan'],content['xspan'],content['align'])
                    if content['widget'] is widgetBefore:
                        do_insertion = True
                else:
                    new_layout.addItem(content['item'],y+insertOffset,x,content['yspan'],content['xspan'],content['align'])
            if do_insertion:
                insertOffset += 1
                do_insertion = False
                if isinstance(widgetTupleAfter,list):
                    self.addToLayout(items=widgetTupleAfter,layout=new_layout)
                else:
                    self.addToLayout(items=[widgetTupleAfter],layout=new_layout)
        if widgetWithLayout is self:
            self._layout = new_layout
        reparent_widget=QWidget()
        reparent_widget.setLayout(layout)
        widgetWithLayout.setLayout(new_layout)
        layout.deleteLater()
        reparent_widget.deleteLater()

    def addToLayout(self,*args,**kwargs):
        items = kwargs.get('items')
        span = kwargs.get('span')
        layout = kwargs.get('layout')

        if not items:
            items = args[0]
            if not items:
                raise ValueError()
        if not layout:
            layout = self._layout
            if not layout:
                raise ValueError()
        if not span:
            span = args[1] if len(args) > 1 else False
        current_row = layout.rowCount()
        current_col = 0
        if not isinstance(items,list):
            self.addToLayout([items],span=span,layout=layout)
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
                    layout.addWidget(i,current_row,current_col,rowspan,colspan,align)
                elif isinstance(i,QLayoutItem):
                    layout.addItem(i,current_row,current_col,rowspan,colspan,align)
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
        return self._layout

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

    def addImageToTitle(self,filename=None,filedata=None):
        if not filename:
            filename = QFileDialog.getOpenFileUrl(self,_('Open image'),QUrl().fromLocalFile(expanduser('~')),'{} (*.png *.jpg *.gif *.svg)'.format(_('Image Files')))
            filename = filename[0]
        else:
            filename = QUrl(filename)
        url = filename.toString()
        filename = filename.toLocalFile()
        image = None
        data = None
        if filedata:
            image = loadPixMapData(filedata)
        else:
            image = QPixmap()
            res = image.load(filename)
            if not res:
                return
            data = dumpPixMapData(image)
        if not 'IMAGE_TITLE' in self.editableItems or not self.editableItems.get('IMAGE_TITLE'):
            label = QLabel(parent=self)
            label.setObjectName('image_title_label')
            self.layoutInsertAfter(self,self.editableItems['TITLE_EDITOR'],(label,Qt.AlignHCenter,True))
        else: # is hidden
            label = self.editableItems['IMAGE_TITLE']
        image = image.scaled(QSize(100,100),Qt.KeepAspectRatio)
        label.setPixmap(image)
        label.setProperty('_filename_',url)
        label.setProperty('_data_',data)
        label.show()
        self.editableItems['IMAGE_TITLE']=label

    def getOptId(self):
        number = self.data.get('optid')
        if not number:
            number = 1
            self.data.setdefault('optid',number)
        else:
            number += 1
            self.data['optid'] = number
        return number

    def addJoinOptionToTest(self):
        number = self.getOptId()
        w = self.newWidgetOption(number)
        name_remove_button = 'JoinOptionRemoveButton#{}'.format(number)
        name_lineedit1 = 'JoinOptionLineEdit1#{}'.format(number)
        name_lineedit2 = 'JoinOptionLineEdit2#{}'.format(number)
        image_button1_name = 'JoinOptionImageButton1#{}'.format(number)
        image_button2_name = 'JoinOptionImageButton2#{}'.format(number)
        tlabel = QLabel("Option",parent=self)
        tlabel.setFixedWidth(self.column_width)
        label = QLabel("\u279C",parent=w)
        label.setFont(QFont('Arial',20,QFont.Bold))
        lineedit1 = QLineEdit(parent=w)
        lineedit1.setObjectName(name_lineedit1)
        lineedit2 = QLineEdit(parent=w)
        lineedit2.setObjectName(name_lineedit2)
        lineedit1.textChanged.connect(self.joinOptionsChanged)
        lineedit2.textChanged.connect(self.joinOptionsChanged)
        button_image1 = QPushButton(QIcon(ICONS['image']),"",parent=w)
        button_image2 = QPushButton(QIcon(ICONS['image']),"",parent=w)
        button_image1.setObjectName(image_button1_name)
        button_image1.setFixedHeight(self.button_size)
        button_image1.setFixedWidth(self.button_size)
        button_image1.setStyleSheet('border:0px;')
        button_image2.setObjectName(image_button2_name)
        button_image2.setFixedHeight(self.button_size)
        button_image2.setFixedWidth(self.button_size)
        button_image2.setStyleSheet('border:0px;')
        button_image1.clicked.connect(self.insertImageOption)
        button_image2.clicked.connect(self.insertImageOption)
        self.data.setdefault('OptionWithImage1#{}'.format(number),'')
        self.data.setdefault('OptionWithImage2#{}'.format(number),'')
        remove_button = QPushButton(QIcon(ICONS['remove']),"",parent=w)
        remove_button.setObjectName(name_remove_button)
        remove_button.clicked.connect(self.removeClicked)
        remove_button.setFixedWidth(self.button_size)
        remove_button.setFixedHeight(self.button_size)
        remove_button.setStyleSheet('border:0px;')
        self.options_declared.setdefault(str(number),{'text1':'','text2':'','img1':'','img2':''})
        self.editableItems.setdefault(image_button1_name,button_image1)
        self.editableItems.setdefault(image_button2_name,button_image2)
        self.editableItems.setdefault(name_remove_button,remove_button)
        self.editableItems.setdefault(name_lineedit1,lineedit1)
        self.editableItems.setdefault(name_lineedit2,lineedit2)
        self.addToLayout([button_image1,lineedit1,(label,Qt.AlignCenter),lineedit2,button_image2,remove_button],layout=w.layout())
        self.addToLayout([tlabel,w],True)
        return number

    def loadJoinOption(self,optionData):
        noption = self.addJoinOptionToTest()
        if not noption:
            raise ValueError()
        text1 = optionData.get('text1')
        text2 = optionData.get('text2')
        pic1 = optionData.get('pic1')
        picname1 = optionData.get('pic1_name')
        pic2 = optionData.get('pic2')
        picname2 = optionData.get('pic2_name')
        if text1:
            lineedit = self.editableItems.get('JoinOptionLineEdit1#{}'.format(noption))
            if lineedit and isinstance(lineedit,QLineEdit):
                lineedit.setText(text1)
            self.options_declared[str(noption)]['text1'] = text1
        if text2:
            lineedit = self.editableItems.get('JoinOptionLineEdit2#{}'.format(noption))
            if lineedit and isinstance(lineedit,QLineEdit):
                lineedit.setText(text2)
            self.options_declared[str(noption)]['text2'] = text2
        if pic1 and picname1:
            imagebutton = self.editableItems.get('JoinOptionImageButton1#{}'.format(noption))
            if imagebutton and isinstance(imagebutton,QPushButton):
                self.manipulateImageIntoButton(imagebutton,picname1,pic1)
        if pic2 and picname2:
            imagebutton = self.editableItems.get('JoinOptionImageButton2#{}'.format(noption))
            if imagebutton and isinstance(imagebutton,QPushButton):
                self.manipulateImageIntoButton(imagebutton,picname2,pic2)

    def newWidgetOption(self,idw=None):
        w = QWidget(self)
        if not idw:
            idw = id(w)
        w.setObjectName('JOption#{}'.format(idw))
        l = QGridLayout()
        w.setLayout(l)
        l.setContentsMargins(0,0,0,0)
        l.setHorizontalSpacing(0)
        return w

    @Slot(int)
    def insertImageOption(self,checked):
        button = self.sender()
        self.manipulateImageIntoButton(button)
        qDebug('click {}'.format(button.objectName()))

    def manipulateImageIntoButton(self,button,filename=None,filedata=None):
        if not isinstance(button,QPushButton):
            raise ValueError()
        name_button = button.objectName()
        if not name_button:
            raise ValueError()
        number = self.getNumber(name_button)
        if not number or not number.isnumeric():
            raise ValueError()
        changing_image = False
        if filename and filedata:
            changing_image = True
        typequestion = self.data.get('type')
        dataname = None
        is_join_activity = True
        answer_num = name_button.split('#')[0][-1]
        if typequestion == _('test_question'):
            is_join_activity = False
            dataname = '{}{}'.format('OptionWithImage#',number)
        elif typequestion == 'join_activity':
            if 'JoinOptionImageButton1#' in name_button:
                dataname = '{}{}'.format('OptionWithImage1#',number)
            elif 'JoinOptionImageButton2#' in name_button:
                dataname = '{}{}'.format('OptionWithImage2#',number)
            else:
                pass
        else:
            pass
        
        if not changing_image and self.data.get(dataname):
            # We are removing
            dialog = QMessageBox()
            dialog.setText(_("Do you wan't to remove image?"))
            dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
            ret = dialog.exec_()
            if ret == QMessageBox.Ok:
                button.setIcon(QIcon(ICONS['image']))
                self.data[dataname] = ''
                if is_join_activity:
                    self.options_declared[number]['img'+answer_num] = ''
                else:
                    self.options_declared[number]['img'] = ''
            else:
                pass
            return

        # No image selected 
        # widget = self.editableItems.get(widgetname)
        # height = widget.height()
        # container = widget.parent()

        if not filename:
            filename = QFileDialog.getOpenFileUrl(self,_('Open image'),QUrl().fromLocalFile(expanduser('~')),'{} (*.png *.jpg *.gif *.svg)'.format(_('Image Files')))
            filename = filename[0]
        else:
            filename = QUrl(filename)
        url = filename.toString()
        filename = filename.toLocalFile()
        image = None
        data = None
        if not filedata:
            image = QPixmap()
            res = image.load(filename)
            if not res:
                return
            data = dumpPixMapData(image)
        else:
            image = loadPixMapData(filedata)
        button.setIcon(QIcon(image))
        button.setProperty('_filename_',url)
        button.setProperty('_data_',data)
        self.data[dataname] =  filename
        if is_join_activity:
            self.options_declared[number]['img'+answer_num] = filename
        else:
            self.options_declared[number]['img'] = filename

    def addOptionToTest(self):
        number = self.getOptId()
        w = self.newWidgetOption(number)
        label = QLabel(_("Option"),parent=w)
        label.setFixedWidth(self.column_width)
        lineEdit = QLineEdit(parent=w)
        lineEdit.textChanged.connect(self.optionsChanged)
        name_button_ok = "OptionButtonOk#{}".format(number)
        name_button_remove = 'OptionButtonRemove#{}'.format(number)
        option_name = 'OptionLineEdit#{}'.format(number)
        image_button_name = 'OptionImageButton#{}'.format(number)
        lineEdit.setObjectName(option_name)
        button_image = QPushButton(QIcon(ICONS['image']),"",parent=w)
        button_image.setObjectName(image_button_name)
        button_image.setFixedHeight(self.button_size)
        button_image.setFixedWidth(self.button_size)
        button_image.setStyleSheet('border:0px;')
        button_image.clicked.connect(self.insertImageOption)
        self.data.setdefault('OptionWithImage#{}'.format(number),'')
        button_ok = QPushButtonTest("",name=name_button_ok,parent=w)
        button_ok.clicked.connect(self.buttonsChanged)
        button_remove = QPushButton(QIcon(ICONS['remove']),"",parent=w)
        button_remove.setObjectName(name_button_remove)
        button_remove.clicked.connect(self.removeClicked)
        button_remove.setFixedHeight(self.button_size)
        button_remove.setFixedWidth(self.button_size)
        button_remove.setStyleSheet('border:0px;')
        self.options_declared.setdefault(str(number),{'text': '', 'trueness': None })
        self.editableItems.setdefault(image_button_name,button_image)
        self.editableItems.setdefault(option_name,lineEdit)
        self.editableItems.setdefault(name_button_ok,button_ok)
        self.editableItems.setdefault(name_button_remove,button_remove)
        self.addToLayout([button_image,lineEdit,button_ok,button_remove],layout=w.layout())
        self.addToLayout([label,w],True)
        return number

    def loadOptionTest(self,optionData):
        noption = self.addOptionToTest()
        if not noption:
            raise ValueError()
        text = optionData.get('text1')
        valid = optionData.get('valid')
        pic = optionData.get('pic1')
        picname = optionData.get('pic1_name')
        if text:
            lineedit = self.editableItems.get('OptionLineEdit#{}'.format(noption))
            if lineedit and isinstance(lineedit,QLineEdit):
                lineedit.setText(text)
            self.options_declared[str(noption)]['text'] = text
        if pic and picname:
            imagebutton = self.editableItems.get('OptionImageButton#{}'.format(noption))
            if imagebutton and isinstance(imagebutton,QPushButton):
                self.manipulateImageIntoButton(imagebutton,picname,pic)
        if valid is None:
            valid = False
        self.options_declared[str(noption)]['trueness'] = valid

    def getNumber(self,name):
        return name.split('#')[1]

    @Slot(int)
    def buttonsChanged(self,checked=None):
        if self.data.get('type') != _('test_question'):
            return

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

    # Only Slot(int) allows sucessful call method sender()
    @Slot(int)
    def optionsChanged(self,text):
        lineedit = self.sender()
        name = lineedit.objectName() if lineedit else None
        if lineedit and name:
            number = self.getNumber(name)
            self.options_declared.setdefault(number,{})
            self.options_declared[number]['text'] = lineedit.text()
        else:
            options = self.getCurrentOptions()
            for name,value in options.items():
                self.options_declared[self.getNumber(name)]['text'] = value.text()

    # Only Slot(int) allows sucessful call method sender()
    @Slot(int)
    def joinOptionsChanged(self,text):
        lineedit = self.sender()
        name = lineedit.objectName() if lineedit else None
        if lineedit and name:
            splname = name.split('#')
            self.options_declared.setdefault(splname[1],{})
            self.options_declared[splname[1]]['text'+splname[0][-1]] = lineedit.text()
        else:
            options = self.getCurrentOptions()
            for name,value in options.items():
                splname = name.split('#')
                self.options_declared.setdefault(splname[1],{})
                self.options_declared[splname[1]]['text'+splname[0][-1]] = value.text()

    def getOptionButtons(self):
        return { k:v for k,v in self.editableItems.items() if 'OptionButtonOk#' in k }

    @Slot(int)
    def removeClicked(self,checked=None):
        sender = self.sender()
        if not sender:
            raise ValueError()
        search_for = None
        delete_items = []
        if self.data['type'] == _('test_question'):
            search_for = 'OptionLineEdit#'
            delete_items = ['OptionLineEdit#','OptionButtonOk#','OptionButtonRemove#']
        elif self.data['type'] == _('join_activity'):
            search_for = 'JoinOptionLineEdit1#' 
            delete_items = ['JoinOptionLineEdit1#','JoinOptionLineEdit2#','JoinOptionRemoveButton#']
        else:
            raise ValueError()
        number = None
        if isinstance(sender,MenuItem):
            numbers = [ int(x.split('#')[1]) for x in self.editableItems.keys() if search_for in x ]
            if numbers:
                last_option = str(max(numbers))
                number = last_option
        else:
            number = self.getNumber(sender.objectName())
            qDebug('removeClicked {} {}'.format(_('from'),number))
        if number:
            wlist = self.findChildren(QWidget,'JOption#{}'.format(number))
            if not wlist:
                raise ValueError()
            self.removeRowItems(wlist[0])
            if self.data['type'] == _('test_question') and number in self.options_declared:
                del self.options_declared[number]
            for pre in ["","1","2"]:
                name = 'OptionWithImage{}#{}'.format(pre,number)
                if name in self.data:
                    del self.data[name]
        self.buttonsChanged()

    def removeRowItems(self,row_or_widget):
        is_row=isinstance(row_or_widget,int)
        is_widget=isinstance(row_or_widget,(QWidget))
        if not (is_row or is_widget):
            raise ValueError()
        position_and_objects = [ (self._layout.getItemPosition(x),self._layout.itemAt(x)) for x in range(self._layout.count()) ]
        row = None
        if is_row:
            row = row_or_widget
        elif is_widget:
            for x in position_and_objects:
                if row_or_widget is x[1].widget():
                    row = x[0][0]

        for x in position_and_objects:
            if row == x[0][0]:
                widget = x[1].widget()
                childrens = self.getChildrenRecursively(widget)
                to_delete=[]
                if childrens:
                    for k,v in self.editableItems.items():
                        if v in childrens:
                            to_delete.append(k)
                for x in to_delete:
                    del self.editableItems[x]
                for w in childrens:
                    w.deleteLater()

    def getChildrenRecursively(self,qobject):
        if isinstance(qobject,QObject):
            ret = [qobject]
            for x in qobject.children():
                ret.extend(self.getChildrenRecursively(x))
            return ret
        else:
            return []

    def getCurrentOptions(self):
        if self.data.get('type') == _('test_question'):
            return { k:v for k,v in self.editableItems.items() if 'OptionLineEdit' in k }
        elif self.data.get('type') == _('join_activity'):
            return { k:v for k,v in self.editableItems.items() if 'JoinOptionLineEdit' in k }

    @Slot()
    def titleEditorChanged(self):
        self.contentChanged.emit(self.id,self.editableItems.get('TITLE_EDITOR').toPlainText())

    def updateTitle(self,content):
        textedit = self.editableItems.get('TITLE_EDITOR')
        if textedit and content and isinstance(content,str):
            textedit.setText(content)

    @Slot(str)
    def controllerQuestions(self,*args,**kwargs):
        qDebug('{} controllerQuestions'.format(_('Called')))
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
                self.removeClicked()
        elif data == 'join_question_add':
            if not self.lock:
                self.addJoinOptionToTest()
        elif data == 'join_question_remove':
            if not self.lock:
                self.removeClicked()
        elif data == 'box_lock':
            self.lock = True
        elif data == 'box_unlock':
            self.lock = False
        elif data == 'add_image':
            self.addImageToTitle()
        elif data == 'del_image':
            label = self.editableItems.get('IMAGE_TITLE')
            if label:
                label.hide()
        elif data == 'dump':
            self.showDumpBox()
        else:
             qDebug("{} '{}' controllerQuestions".format(_('No action declared for'),data))
        self.do_lock()

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
                    raise ValueError("{} {}".format(_("Can't lock"),v))

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
                    raise ValueError("{} {}".format(_("Can't unlock"),v))

            buttons = self.menu.getButtons() 
            for name,b in buttons.items():
                if name == 'unlock':
                    b.setDisabled(True)
                else:
                    b.setEnabled(True)
        
        # CHECKS AFTER TOOLBAR CLICK

        # JOption is deleted asynchronously, here we need to know if row is deleted
        # options = [ x for x in self.children() if isinstance(x,QWidget) and 'JOption' in x.objectName() ]
        options = self.getCurrentOptions()
        if not options:
            button_remove = self.findChild(QToolButton,'remove_option')
            if button_remove:
                button_remove.setDisabled(True)

        if self.data.get('type') != _('single_question'):
            if options:
                self.configureSlider(1,len(options))
            slider = self.findChild(QAction,'action_slider')
            slider_label = self.findChild(QAction,'action_label_slider')
            title_slider = self.findChild(QAction,'action_title_slider')
            for x in [slider,slider_label,title_slider]:
                if not x:
                    continue
                if options:
                    x.setVisible(True)
                else:
                    x.setVisible(False)
        # Enable/Disable remove image button from toolbar
        button_delete = self.findChild(QToolButton,'delete_image')
        if button_delete:
            if 'IMAGE_TITLE' in self.editableItems and self.editableItems.get('IMAGE_TITLE') != None and not self.editableItems.get('IMAGE_TITLE').isHidden():
                button_delete.setDisabled(False)
            else:
                button_delete.setDisabled(True)
        self.buttonsChanged()

    def addSlider(self,container,label,callback):
        title = QLabel(label)
        title.setStyleSheet('margin-right: 5px')
        slider = QSlider()
        slider.setOrientation(Qt.Horizontal)
        slider.setObjectName('slider')
        slider.setFixedWidth(80)
        slider.setMinimum(1)
        slider.setMaximum(1)
        label = QLabel('0/0')
        label.setObjectName('slider_label')
        label.setFont(QFont('Arial',10,QFont.Normal))
        label.setStyleSheet('margin-left: 5px')
        a = container.addWidget(title)
        a.setObjectName('action_title_slider')
        b = container.addWidget(slider)
        b.setObjectName('action_slider')
        c = container.addWidget(label)
        c.setObjectName('action_label_slider')
        slider.valueChanged.connect(callback)
        self.editableItems['SLIDER_CONTROL'] = slider
        self.editableItems['SLIDER_LABEL'] = label
        slider.valueChanged.emit(1)

    def updateLinesForAnswer(self,value):
        self.empty_lines_for_answer = value
        self.editableItems['EMPTY_LINES_LABEL'].setText('{}: {}'.format(_('Empty lines for answer'),value))

    def setSliderValue(self,value):
        slider = self.editableItems['SLIDER_CONTROL']
        slider.setSliderPosition(value)
        slider.valueChanged.emit(value)

    @Slot(int)
    def sliderChanged(self, value=None):
        if value is None:
            return
        slider = self.editableItems['SLIDER_CONTROL']
        label = self.editableItems['SLIDER_LABEL']
        label.setText("{}/{}".format(value,slider.maximum()))
        type_question = self.data.get('type')
        if type_question == _('single_question'):
            self.updateLinesForAnswer(value)
        elif type_question == _('test_question'):
            for x in self.options_declared:
                old_value = self.options_declared[x]['trueness']
                if self.count_trues > value or not old_value:
                    self.options_declared[x]['trueness'] = None
            self.count_trues = value
            self.buttonsChanged()

    def configureSlider(self,min=1,max=1,value=None):
        slider = self.editableItems.get('SLIDER_CONTROL')
        if slider:
            if min and min < 1:
                min = 1
            if max and max < 1:
                max = 1
            if not value:
                value = slider.value()
            else:
                if value < min:
                    value = min
                elif value > max:
                    value = max
            slider.setMinimum(min)
            slider.setMaximum(max)
            slider.setSliderPosition(value)
            slider.valueChanged.emit(slider.value())

    def makeQuestionTypeLayout(self):
        typeQuestion = self.data.get('type')
        if not typeQuestion:
            qDebug(_('Empty type for question received'))
        if typeQuestion == _('single_question'):
            self.menu.emptyMenu()
            self.editableItems['EMPTY_LINES_LABEL'] = QLabel()
            elements = ["{}(add_image)|image".format(_('Add image')),"{}(del_image)|image_missing".format(_('Delete image')),"{}(box_lock)|lock".format(_('Lock')),"{}(box_unlock)|unlock".format(_('Unlock'))]
            if VIEW_DUMP_OPTION:
                elements.insert(0,"{}(dump)|high".format('Dump'))
            self.menu.addMenuItem(elements)
            self.menu.itemActivation.connect(self.controllerQuestions)
            self.addSlider(self.menu.menu,'{}:'.format(_('Empty lines')),self.sliderChanged)
            self.addToLayout(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Fixed))
            self.addTitleEditor(self.data.get('initial_content'))
            self.addToLayout([(self.editableItems['EMPTY_LINES_LABEL'],Qt.AlignCenter,True)])
            self.configureSlider(1,30)
            self.do_lock()
        elif typeQuestion == _('test_question'):
            self.menu.emptyMenu()
            elements = ["{}(test_question_add)|add".format(_('Add option')),"{}(test_question_remove)|remove".format(_('Remove option')),"{}(add_image)|image".format(_('Add image')),"{}(del_image)|image_missing".format(_('Delete image')),"{}(box_lock)|lock".format(_('Lock')),"{}(box_unlock)|unlock".format(_('Unlock'))]
            if VIEW_DUMP_OPTION:
                elements.insert(0,"{}(dump)|high".format(_('Dump')))
            self.menu.addMenuItem(elements)
            self.menu.itemActivation.connect(self.controllerQuestions)
            self.addSlider(self.menu.menu,'{}:'.format(_('Valid')),self.sliderChanged)
            self.addTitleEditor(self.data.get('initial_content'))
            self.do_lock()
        elif typeQuestion == _('join_activity'):
            self.menu.emptyMenu()
            elements = ["{}(join_question_add)|add".format(_('Add option')),"{}(join_question_remove)|remove".format(_('Remove option')),"{}(add_image)|image".format(_('Add image')),"{}(del_image)|image_missing".format('Delete image'),"{}(box_lock)|lock".format(_('Lock')),"{}(box_unlock)|unlock".format(_('Unlock'))]
            if VIEW_DUMP_OPTION:
                elements.insert(0,"{}(dump)|high".format(_('Dump')))
            self.menu.addMenuItem(elements)
            self.menu.itemActivation.connect(self.controllerQuestions)
            self.addTitleEditor(self.data.get('initial_content'))
            self.do_lock()
            pass
        else:
            qDebug('{} "{}" {}, {}'.format(_('type for question'),typeQuestion,_('unknown'),_('skipping')))

    def dumpFileData(self,url):
        f = QFile(QUrl(url).toLocalFile())
        if f.exists() and f.open(QIODevice.ReadOnly):
            return qCompress(f.readAll()).toBase64().data().decode()
        else:
            f = QFile(url)
            if f.exists() and f.open(QIODevice.ReadOnly):
                return qCompress(f.readAll()).toBase64().data().decode()
        return None

    def showDumpBox(self):
        boxInfo = self.dumpBox()
        if not boxInfo:
            return
        d = QDialog(self,Qt.Window)
        d.setFixedSize(QSize(800,600))
        d.setLayout(QVBoxLayout())
        te = QTextEdit()
        d.layout().addWidget(te)
        text = pp(boxInfo)
        te.setText('{}'.format(text))
        d.exec()

    def dumpBox(self):
        dumpInfo = { 
            'type': None,
            'title': None,
            'title_pic': None,
            'title_picname': None,
            'empty_lines': None,
            'locked': None,
            'nvalid': None,
            'options': None
        }
        optionInfo = {
            'type': None,
            'order': None,
            'pic1': None,
            'pic1_name': None,
            'pic2': None,
            'pic2_name': None,
            'text1': None,
            'text2': None,
            'valid': None
        }
        boxInfo = deepcopy(dumpInfo)
        boxInfo['type'] = self.data.get('type')
        boxInfo['title'] = self.editableItems['TITLE_EDITOR'].toPlainText()
        lbl = self.findChild(QLabel,'image_title_label')
        if lbl and not lbl.isHidden():
            filename = lbl.property('_filename_')
            boxInfo['title_picname'] = filename
            boxInfo['title_pic'] = self.dumpFileData(filename)
            if not boxInfo['title_pic']:
                data = lbl.property('_data_')
                boxInfo['title_pic'] = data
        boxInfo['empty_lines'] = self.empty_lines_for_answer
        boxInfo['locked'] = self.lock
        boxInfo['nvalid'] = self.count_trues
        # options = self.getCurrentOptions()
        # noptions = sorted(list(set([ self.getNumber(x) for x in options.keys() ])))
        if boxInfo['type'] != _('single_question'):
            boxInfo['options'] = []
            # for o in noptions:
            for o in sorted(self.options_declared.keys()):
                optInfo = deepcopy(optionInfo)
                optInfo['type'] = boxInfo['type']
                # optInfo['order'] = noptions.index(o)
                optInfo['order'] = o
                option = self.options_declared.get(o)
                optInfo['valid'] = option.get('trueness') 
                if boxInfo['type'] == _('test_question'):
                    optInfo['text1'] = option.get('text')
                    if option.get('img'):
                        optInfo['pic1_name'] = QUrl().fromLocalFile(option.get('img')).toString()
                        pixdata = self.dumpFileData(optInfo['pic1_name'])
                        if pixdata:
                            optInfo['pic1'] = pixdata
                        else:
                            btn = self.findChild(QPushButton,'OptionImageButton#{}'.format(o))
                            if btn:
                                pixdata = btn.property('_data_')
                                optInfo['pic1'] = pixdata
                            else:
                                raise ValueError()
                elif boxInfo['type'] == _('join_activity'):
                    for n in ["1","2"]:
                        optInfo['text'+n] = option.get('text'+n)
                        optInfo['text'+n] = option.get('text'+n)
                        if option.get('img'+n):
                            optInfo['pic{}_name'.format(n)] = QUrl().fromLocalFile(option.get('img'+n)).toString()
                            pixdata = self.dumpFileData(optInfo['pic{}_name'.format(n)])
                            if pixdata:
                                optInfo['pic'+n] = pixdata
                            else:
                                btn = self.findChild(QPushButton,'JoinOptionImageButton{}#{}'.format(n,o))
                                if btn:
                                    pixdata = btn.property('_data_')
                                    optInfo['pic'+n] = pixdata
                                else:
                                    raise ValueError()
                else:
                    pass
                boxInfo['options'].append(optInfo)
        return boxInfo

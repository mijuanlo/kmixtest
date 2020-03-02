from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Helper import Helper
from .Config import ICONS, UI, NATIVE_THREADS
from .TableHelper import tableHelper
from .GridHelper import gridHelper
from .HelperPDF import helperPDF
from .Persistence import Persistence
from .MenuItem import MenuItem
from .Util import dumpPixMapData,loadPixMapData

from os.path import expanduser
from copy import deepcopy

#AllowedQuestionTypes = ["Single question","Test question","Join activity"]
from .QuestionType import Question
# Main class of application
class AppMainWindow(QApplication):    
    def __init__(self):
        super().__init__([])
        try:
            self.window = self.loadUi()
            left_policy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
            left_policy.setHorizontalStretch(2)
            right_policy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
            right_policy.setHorizontalStretch(3)
            self.window.scrollAreaQuestions.setSizePolicy(left_policy)
            self.window.scrollAreaAnswers.setSizePolicy(right_policy)
            self.menu = MenuItem(menu=self.window.menubar,parent=self)
            self.menu.itemActivation.connect(self.menuController)
            #self.window.gridEdition.addItem(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Expanding))
            self.window.show()
            self.bind_toolbar_actions(Question().allNames())
            self.tableQuestions = tableHelper(self.window.tableWidgetQuestions, self)
            self.tableQuestions.editingQuestion.connect(self.editingQuestion)
            self.tableQuestions.questionChanged.connect(self.questionChanged)
            self.window.scrollAreaAnswers.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )

            self.scroll = gridHelper(self.window.gridEdition, self)
            self.scroll.boxIsUpdating.connect(self.updateTitleRow)
            self.tableQuestions.tableChanged.connect(self.tableQuestionsChanged)
            self.window.previewButton.clicked.connect(self.clickedPreview)
            self.window.previewButton.hide()
            self.tableQuestions.rowSelection.connect(self.scroll.showQuestion)
            self.sheet = None
            self.aboutToQuit.connect(self.exitting)
            self.persistence = Persistence(debug=True)
            self.menu.addMenuItem([{"Project":["New(menu_new)|new","-","Load exam(menu_load_exam)","Load template(menu_load_template)","-","Save(menu_save)|save","Save as(menu_save_as)|save","Save as template(menu_save_as_template)|save","-","Exit(menu_exit_app)|exit"]},{"Mixer":["Configure header(menu_configure_header)","Configure output(menu_configure_output)","Generate Mix(menu_generate_mix)"]},{"Print":["Print preview(menu_print_preview)|print","Print Exam(menu_print_exam)|print"]}])
            self.tableQuestions.pool.start_threads()
            self.editing_question = None
            self.n_models = 1
            self.alter_models = False
            self.header_info = {}
            self.current_filename = None
            self.aborting = False
            # self.menuController('menu_print_exam')
            # self.exitting()
        except Exception as e:
            print("Exception when initializing, {}".format(e))
            self.exitting()

    @Slot()
    def exitting(self):
        global NATIVE_THREADS
        self.aborting = True
        qDebug("Exitting")
        if self.tableQuestions:
            if self.tableQuestions.pool:
                self.tableQuestions.pool.terminate = True
                self.tableQuestions.pool.abort()
                if NATIVE_THREADS:
                    self.tableQuestions.pool.threadpool.clear()
        self.quit()

    def rowEditionPermitted(self,row_uuid):
        box = self.scroll.getBoxFromRowId(row_uuid)
        if box.lock:
            qDebug('Edition not permitted, box locked')
            return False
        return True

    @Slot()
    def tableQuestionsChanged(self):
        data = self.tableQuestions.getCellContent(named=True)
        self.scroll.syncMapTableData(data)

    @Slot(int)
    def editingQuestion(self, row):
        qDebug("Editing {}".format(row))
        self.editing_question = row

    @Slot(int)
    def questionChanged(self,row=None):
        if row is not None and self.editing_question == row:
            self.editing_question = None
            qDebug("Question Changed {}".format(row))
            self.tableQuestionsChanged()

    @Slot(str,str)
    def updateTitleRow(self,row_uuid,content):
        # qDebug("Updating title col")
        self.tableQuestions.updateTitleRow(row_uuid,content)

    def initializePrinting(self):
        if not self.sheet:
            self.sheet = helperPDF(parent=self)
        self.sheet.setHeaderInfo(self.header_info)
        examData = self.buildExamData()
        exam = examData.get('examdata')
        if exam:
            self.sheet.setExamData(exam)

    @Slot(int)
    def clickedPreview(self,checked):
        qDebug("Preview clicked!")
        self.initializePrinting()
        self.sheet.openWidget()

    def print_exam(self):
        self.initializePrinting()
        self.sheet.writePDF()

    def loadUi(self):
        global UI
        ui_file = QFile(UI)
        ui_file.open(QFile.ReadOnly)
        ui_loader = QUiLoader(self)
        window = ui_loader.load(ui_file)
        ui_file.close()
        return window

    def bind_toolbar_actions(self,actions):
        global ICONS
        if isinstance(actions,str):
            actions = [actions]
        elif isinstance(actions,list):
            pass
        else:
            raise ValueError()
        self.window.toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        for a in actions:
            name = a
            q = Question().search(name)
            if not q:
                continue
            iconname = q.getNameId()
            if name in ICONS:
                iconname = name
            elif iconname in ICONS:
                pass
            else:
                iconname = 'exit'
            action = Helper.genAction(name=q.getName(),fn=self.menuController,data=q.getNameId(),icon=QIcon(ICONS[iconname]),tip=name,parent=self)
            self.window.toolBar.addAction(action)

    def openfiledialog(self):
        f = QFileDialog().getOpenFileName(None,self.tr("Open Exam"),expanduser("~"),self.tr("Exam files (*.kmt)"))
        return f[0] if f else None

    def savefiledialog(self):
        f = QFileDialog().getSaveFileName(None,self.tr("Save Exam"),expanduser("~"),self.tr("Exam files (*.kmt)"))
        return f[0] if f else None

    def buildExamData(self, template=False):
        e = {
            'header': None,
            'config': None,
            'examdata': None
        }
        exam = deepcopy(e)
        if not template:
            examData = []
            examDataRow = {
                'type': None,
                'order': None,
                'fixed': None,
                'linked': None,
                'title': None
            }
            self.tableQuestionsChanged()
            model = self.tableQuestions.dumpTableModel()
            boxes = self.scroll.dumpBoxes()
            if len(model) != len(boxes):
                raise ValueError()
            for row in model:
                if len(row) != 6:
                    raise ValueError()
                order,fixed,linked,title,typeq,uid = row
                box = boxes.get(uid) 
                empty = False
                if not box:
                    if uid in boxes.keys():
                        # box has't been edited
                        empty = True
                    else:
                        raise ValueError()
                if not empty and typeq != box.get('type'):
                    raise ValueError()
                datarow = deepcopy(examDataRow)
                datarow['type'] = typeq
                datarow['order'] = order
                datarow['fixed'] = fixed
                datarow['linked'] = linked
                datarow['title'] = title
                if not empty:
                    for k,v in box.items():
                        datarow.setdefault(k,v)
                examData.append(datarow)
            if examData:
                exam['examdata'] = examData
        header = self.buildHeaderData()
        if header:
            exam['header'] = header
        config = self.buildConfig()
        if config:
            exam['config'] = config

        return exam

    def buildHeaderData(self):
        headerData = {
            'north': None,
            'west': None,
            'south': None,
            'east': None
        }
        h = deepcopy(headerData)
        h['north'] = deepcopy(self.header_info.get('north'))
        h['west'] = deepcopy(self.header_info.get('west'))
        h['south'] = deepcopy(self.header_info.get('south'))
        h['east'] = deepcopy(self.header_info.get('east'))
        return h

    def buildConfig(self):
        config =  { 
            'nmodels': self.n_models,
            'alter': self.alter_models,
        }
        return config

    def loadConfig(self,configdata):
        if not isinstance(configdata,dict):
            raise ValueError()
        ks = configdata.keys()
        for k in ['nmodels','alter']:
            if k not in ks:
                raise ValueError()
        nmodels = configdata.get('nmodels')
        alter = configdata.get('alter')
        self.n_models = nmodels
        self.alter_models = alter

    def useExamData(self,examData):
        model = {}
        if not examData:
            raise ValueError()
        i=0
        for row in examData:
            order = row.get('order')
            if order is None:
                raise ValueError()
            model.setdefault(order,i)
            i+=1
        sk = sorted(model.keys())
        for x in sk:
            nrow = model.get(x)
            row = examData[nrow]
            name = row.get('title')
            fixed = row.get('fixed')
            linked = row.get('linked')
            typeq = row.get('type')
            uuid = self.tableQuestions.addItemWithState(name,bool(fixed),bool(linked),typeq)
            row.setdefault('uuid',uuid)
        self.tableQuestionsChanged()
        for x in sk:
            nrow = model.get(x)
            row = examData[nrow]
            self.scroll.loadBox(row)
        self.scroll.hide_all_boxes()
        return None

    @Slot(int)
    def clickFromHeaderMenu(self,checked):
        button = self.sender()
        self.header_menu_actions.append(button)
        container_button = button.parent()
        scroll_viewport = container_button.parent()
        table = scroll_viewport.parent()
        name_container = container_button.objectName()
        ncontainer = name_container.split('#')[1]
        if button.text() == 'Image':
            filename = QFileDialog.getOpenFileUrl(container_button,'Open image',QUrl().fromLocalFile(expanduser('~')),'Image Files (*.png *.jpg *.gif *.svg)')
            filename = filename[0]
            url = filename.toString()
            filename = filename.toLocalFile()
            image = QPixmap()
            res = image.load(filename)
            if res == False:
                qDebug('filename {} invalid'.format(filename))
                return
            else:
                qDebug('filename {} valid'.format(filename))
                data = dumpPixMapData(image)
                found = False
                for x in container_button.children():
                    if isinstance(x,QLabel):
                        found = x
                        break;
                if not found:
                    la = QLabel()
                    la.setObjectName('image#{}'.format(ncontainer))
                    # image = image.scaled(container_button.rect().size(),Qt.KeepAspectRatio)
                    image = image.scaled(QSize(60,60),Qt.KeepAspectRatio)
                    la.setProperty('_filename_',url)
                    la.setProperty('_data_',data)
                    la.setPixmap(image)
                    container_button.layout().addWidget(la)
                else:
                    la = found
                    image = image.scaled(container_button.rect().size(),Qt.KeepAspectRatio)
                    la.setProperty('_filename_',filename)
                    la.setProperty('_data_',data)
                    la.setPixmap(image)
                    la.show()
        else:
            found = False
            for x in container_button.children():
                if isinstance(x,QTextEdit):
                    found = x
                    break
            if not found:
                le = QTextEdit()
                le.setObjectName('text_edit#'.format(ncontainer))
                container_button.layout().addWidget(le)
                le.setFocus()
            else:
                le = found
                le.setText("")
                le.show()
                le.setFocus()
        for x in container_button.children():
            if isinstance(x,QPushButton):
                x.hide()

    @Slot(int)
    def acceptHeaderMenu(self,checked):
        for x in ['north','west','east','south']:
            self.header_info.setdefault(x,None)
            child = self.dialog_header.findChild(QWidget,'button_container#{}'.format(x))
            if not child:
                raise ValueError()
            for c in child.children():
                if not isinstance(c,QWidget) or c.isHidden():
                    continue
                else:
                    if isinstance(c,QTextEdit):
                        self.header_info[x] = {'type': 'text' , 'content': c.toPlainText() }
                    elif isinstance(c,QLabel):
                        self.header_info[x] = {'type': 'image', 'content': c.property('_filename_'), 'data': c.property('_data_') }
                    elif isinstance(c,QPushButton):
                        self.header_info[x] = None
                    else:
                        pass
        self.window.setEnabled(True)
        self.dialog_header.deleteLater()
        self.dialog_header_actions.deleteLater()
    
    @Slot(int)
    def cancelHeaderMenu(self,checked):
        self.window.setEnabled(True)
        self.dialog_header.deleteLater()
        self.dialog_header_actions.deleteLater()

    @Slot(int)
    def undoHeaderMenu(self,checked):
        if len(self.header_menu_actions):
            last_thing = self.header_menu_actions[-1]
            del self.header_menu_actions[-1]
            if isinstance(last_thing,QPushButton):
                container = last_thing.parent()
                for x in container.children():
                    if isinstance(x,QPushButton):
                        x.show()
                    elif isinstance(x,(QTextEdit,QLabel)):
                        x.hide()
                    else:
                        pass
            else:
                pass

    @Slot(int)
    def clearHeaderMenu(self,checked):
        for x in ['north','west','south','east']:
            child = self.dialog_header.findChild(QWidget,'button_container#{}'.format(x))
            if not child:
                raise ValueError()
            for c in child.children():
                if not isinstance(c,QWidget):
                    continue
                else:
                    if isinstance(c,(QTextEdit,QLabel)):
                        c.hide()
                    elif isinstance(c,QPushButton):
                        c.show()
                    else:
                        pass

    def loadHeader(self,headerdata):
        if not isinstance(headerdata,dict):
            raise ValueError()
        ks = headerdata.keys()
        for k in ['north','west','south','east']:
            if k not in ks:
                raise ValueError
        north = headerdata.get('north')
        west = headerdata.get('west')
        south = headerdata.get('south')
        east = headerdata.get('east')
        for x in ['north','west','east','south']:
            self.header_info.setdefault(x,{})
        self.header_info['west'] = deepcopy(west)
        self.header_info['north'] = deepcopy(north)
        self.header_info['east'] = deepcopy(east)
        self.header_info['south'] = deepcopy(south)

    def generateHeaderMenu(self):
        self.header_menu_actions = []
        self.window.setEnabled(False)
        self.dialog_header = QDialog(self.window,Qt.Tool)
        flags = Qt.Tool|Qt.CustomizeWindowHint|Qt.WindowTitleHint
        self.dialog_header.setWindowFlags(flags)
        self.dialog_header_actions = QDialog(self.window,Qt.Tool)
        self.dialog_header_actions.setWindowFlags(flags)
        #self.dialog_header.resize(500,200)
        self.dialog_header_actions.setLayout(QVBoxLayout())
        self.dialog_header.setWindowTitle('Configure header')
        self.dialog_header.setGeometry(self.window.geometry().x()+50,self.window.geometry().y()+(self.window.height()/2)-100,500,200)
        self.dialog_header_actions.setGeometry(self.window.geometry().x()+self.window.width()-100-50,self.dialog_header.geometry().y(),75,100)
        table = QTableWidget(2,3)
        table.setObjectName('configure_header_table')
        layout = QGridLayout()
        self.dialog_header.setLayout(layout)
        # layout.setSpacing(0)
        # layout.setContentsMargins(0,0,0,0)
        layout.addWidget(table)
        contents = {}
        for x in ['north','west','east','south']:
            contents.setdefault(x,QWidget(parent=self.dialog_header))
            contents[x].setObjectName('button_container#{}'.format(x))
            layout_w = QVBoxLayout()
            layout_w.setAlignment(Qt.AlignCenter)
            contents[x].setLayout(layout_w)
            btn1 = QPushButton('Image',parent=contents[x])
            btn2 = QPushButton('Text',parent=contents[x])
            btn1.setFocusPolicy(Qt.NoFocus)
            btn2.setFocusPolicy(Qt.NoFocus)
            layout_w.addWidget(btn1)
            layout_w.addWidget(btn2)
            btn1.clicked.connect(self.clickFromHeaderMenu)
            btn2.clicked.connect(self.clickFromHeaderMenu)
            if x in self.header_info and self.header_info.get(x):
                content = self.header_info.get(x)
                if 'type' in content:
                    btn1.hide()
                    btn2.hide()
                    if content['type'] == 'text':
                        le = QTextEdit()
                        le.setObjectName('text_edit#'.format(x))
                        le.setText(content['content'])
                        layout_w.addWidget(le)
                    elif content['type'] == 'image':
                        la = QLabel()
                        url = QUrl(content['content'])
                        image = None
                        data = None
                        if url.isValid() and url.scheme() == 'file' and url.isLocalFile():
                            filename = url.toLocalFile()
                            image = QPixmap()
                            res = image.load(filename)
                            if res:
                                data = dumpPixMapData(image)
                            else:
                                raise ValueError()
                        else:
                            data = content['data']
                            if data:
                                image = loadPixMapData(data)
                            else:
                                raise ValueError()
                        la.setObjectName('image#{}'.format(x))
                        #image = image.scaled(contents[x].rect().size(),Qt.KeepAspectRatio)
                        image = image.scaled(QSize(60,60),Qt.KeepAspectRatio)
                        la.setProperty('_filename_',url)
                        la.setProperty('_data_',data)
                        la.setPixmap(image)
                        layout_w.addWidget(la)
                    else:
                        pass
        contents['actions'] = QWidget(parent=self.dialog_header_actions)
        contents['actions'].setObjectName('button_container#e')
        layout_actions = QVBoxLayout()
        contents['actions'].setLayout(layout_actions)
        btn1 = QPushButton('Ok',parent=contents['actions'])
        btn2 = QPushButton('Cancel',parent=contents['actions'])
        btn3 = QPushButton('Undo',parent=contents['actions'])
        btn4 = QPushButton('Clear',parent=contents['actions'])
        btn1.clicked.connect(self.acceptHeaderMenu)
        btn2.clicked.connect(self.cancelHeaderMenu)
        btn3.clicked.connect(self.undoHeaderMenu)
        btn4.clicked.connect(self.clearHeaderMenu)
        btn1.setFocusPolicy(Qt.NoFocus)
        btn2.setFocusPolicy(Qt.NoFocus)
        btn3.setFocusPolicy(Qt.NoFocus)
        btn4.setFocusPolicy(Qt.NoFocus)
        layout_actions.addWidget(btn1)
        layout_actions.addWidget(btn2)
        layout_actions.addWidget(btn3)
        layout_actions.addWidget(btn4)
        table.setFocusPolicy(Qt.NoFocus)
        table.setCellWidget(0,0,contents['west'])
        table.setCellWidget(0,1,contents['north'])
        table.setCellWidget(0,2,contents['east'])
        table.setCellWidget(1,0,contents['south'])
        table.setSpan(1,0,1,3)
        self.dialog_header_actions.layout().addWidget(contents['actions'])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers | QAbstractItemView.NoState)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        self.dialog_header.show()
        self.dialog_header_actions.show()

    def generateMixMenu(self):
        def updateValues(dialog):
                le = dialog.findChild(QLineEdit,'n_models')
                c = dialog.findChild(QCheckBox,'alter_models')
                self.n_models = int(le.text())
                self.alter_models = c.checkState() == Qt.CheckState.Checked
                dialog.close()

        dialog = QDialog(self.window,Qt.Window)
        dialog.setModal(True)
        dialog.setWindowTitle('Generate mix')
        dialog.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)
        l1 = QLabel("Number disctinct models:")
        le = QLineEdit()
        le.setObjectName('n_models')
        le.setMaxLength(1)
        le.setFixedWidth(le.sizeHint().height())
        le.setInputMask("D")
        le.setText(str(self.n_models))
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(l1)
        hlayout1.addWidget(le)
        l2 = QLabel("Alter answer order:")
        c = QCheckBox()
        c.setObjectName('alter_models')
        state = Qt.Unchecked
        if self.alter_models:
            state = Qt.Checked
        c.setCheckState(state)
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(l2)
        hlayout2.addWidget(c,0,Qt.AlignRight)
        hlayout3 = QHBoxLayout()
        b1 = QPushButton('Ok')
        b2 = QPushButton('Close')
        b1.setCheckable(False)
        b1.clicked.connect(lambda: updateValues(dialog))
        b2.setCheckable(False)
        b2.clicked.connect(lambda: dialog.close())
        hlayout3.addWidget(b1,0,Qt.AlignRight)
        hlayout3.addWidget(b2,0,Qt.AlignRight)
        w1 = QWidget()
        w2 = QWidget()
        w3 = QWidget()
        w1.setLayout(hlayout1)
        w2.setLayout(hlayout2)
        w3.setLayout(hlayout3)
        vlayout.addWidget(w1)
        vlayout.addWidget(w2)
        vlayout.addWidget(w3,0,Qt.AlignRight)
        dialog.exec()

    @Slot(str)
    def menuController(self,*args,**kwargs):
        qDebug('Called menuController')
        if not args:
            if self.sender():
                data = self.sender().data()
            else:
                raise ValueError()
        else:
            data = args[0]
        if not data:
            raise ValueError()
        qDebug('Menu "{}" click'.format(data))
        if data == 'menu_exit_app':
            self.exitting()
        elif data == 'menu_load_exam':
            filename = self.openfiledialog()
            if filename:
                self.tableQuestions.clearTable()
                examData = self.persistence.loadExam(filename)
                if not examData:
                    raise ValueError()
                if not isinstance(examData,dict):
                    raise ValueError()
                header = examData.get('header')
                if header:
                    self.loadHeader(header)
                config  = examData.get('config')
                if config:
                    self.loadConfig(config)
                questions = examData.get('examdata')
                if questions:
                    self.useExamData(questions)
        elif data == 'menu_new':
            self.tableQuestions.clearTable()
            self.header_info = {}
            self.n_models = 1
            self.alter_models = False
            self.current_filename = None
        elif data == 'menu_save':
            if self.current_filename:
                examData = self.buildExamData()
                result = self.persistence.saveExam(self.current_filename,examData)
            else:
                self.menuController('menu_save_as')
        elif data == 'menu_save_as':
            filename = self.savefiledialog()
            if filename:
                examData = self.buildExamData()
                result = self.persistence.saveExam(filename,examData)
                self.current_filename = filename
        elif data == 'menu_save_as_template':
            filename = self.savefiledialog()
            if filename:
                examData = self.buildExamData(template=True)
                result = self.persistence.saveExam(filename,examData)
                self.current_filename = filename
        elif data == 'menu_print_preview':
            self.clickedPreview(True)
        elif data in Question().allTypes():
            self.editing_question = None
            self.window.statusbar.showMessage("New question: {}".format(data),10*1000)
            q = Question().search(data)
            self.tableQuestions.addItem(q.getName())
        elif data == 'menu_print_exam':
            self.print_exam()
        elif data == 'menu_generate_mix':
            self.generateMixMenu()
        elif data == 'menu_configure_header':
            self.generateHeaderMenu()
        elif data == 'menu_load_template':
            filename = self.openfiledialog()
            if filename:
                self.tableQuestions.clearTable()
                examData = self.persistence.loadExam(filename)
                if not examData:
                    raise ValueError()
                if not isinstance(examData,dict):
                    raise ValueError()
                header = examData.get('header')
                if header:
                    self.loadHeader(header)
                config  = examData.get('config')
                if config:
                    self.loadConfig(config)
        else:
            qDebug("No action declared for '{}' menuaction".format(data))
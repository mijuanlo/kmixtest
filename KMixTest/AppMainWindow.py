from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Helper import Helper
from .Config import _, ICONS, UI, NATIVE_THREADS
from .TableHelper import tableHelper
from .GridHelper import gridHelper
from .HelperPDF import helperPDF
from .Persistence import Persistence
from .MenuItem import MenuItem
from .Util import dumpPixMapData,loadPixMapData
from .CustomTranslator import CustomTranslator
from .MainWindow import Ui_MainWindow
from .HeaderController import HeaderController

from os.path import expanduser
from os import urandom
from copy import deepcopy
from random import randint,shuffle,sample,choice,seed

import os.path

from .QuestionType import Question


class MainWindow(QMainWindow,Ui_MainWindow):
    closeRequested = Signal()
    def __init__(self):
        super(MainWindow,self).__init__()
        self.setupUi(self)
    def closeEvent(self, event):
        self.closeRequested.emit()

# Main class of application
class AppMainWindow(QApplication):    
    def __init__(self,load_filename=None):
        super().__init__([])
        try:
            self.debug = False
            self.debug_translations = False or self.debug
            self.window = self.loadUi()
            self.setWindowIcon(QIcon(ICONS['application']))
            self.translator = self.initTranslator()
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
            self.window.closeRequested.connect(self.exitting)
            self.persistence = Persistence(debug=True)
            self.menu.addMenuItem(
                [
                    {_("Project"):
                        [
                            "{}(menu_new)|new".format(_('New')),
                            "-",
                            "{}(menu_load_exam)|open".format(_('Load exam')),
                            "{}(menu_load_template)|open".format(_('Load template')),
                            "-",
                            "{}(menu_save)|save".format(_('Save')),
                            "{}(menu_save_as)|save".format(_('Save as')),
                            "{}(menu_save_as_template)|save".format(_('Save as template')),
                            "-","{}(menu_exit_app)|exit".format(_('Exit'))
                        ]
                    },
                    {_("Mixer"):
                        [
                            "{}(menu_configure_header)|header".format(_('Configure header')),
                            "{}(menu_configure_output)|configure".format(_('Configure output')),
                            "{}(menu_generate_mix)|merge".format(_('Generate Mix'))
                        ]
                    },
                    {_("Print"):
                        [
                            "{}(menu_print_preview)|print".format(_('Print preview')),
                            "{}(menu_print_exam)|print".format(_('Print Exam'))
                        ]
                    }
                ]
            )
            self.tableQuestions.pool.start_threads()
            self.editing_question = None
            self.n_models = 1
            self.alter_models = False
            self.with_solutionary = True
            self.dialogheader = None
            self.headerData = None
            self.examData = None
            self.current_filename = None
            self.output_filename = None
            self.aborting = False
            self.currentExam = None
            if load_filename:
                self.autoloadfilename = load_filename
                self.menuController('menu_load_exam')
                #self.menuController('menu_configure_header')
                #self.menuController('menu_print_preview')
                #self.menuController('menu_print_exam')
            else:
                self.autoloadfilename = None
            # self.exitting()
        except Exception as e:
            print("{}, {}".format(_('Exception while initializing'),e))
            self.exitting()

    def initTranslator(self):
        translator = CustomTranslator(debug=self.debug_translations)
        self.installTranslator(translator)
        return translator

    @Slot()
    def exitting(self):
        global NATIVE_THREADS
        self.aborting = True
        qDebug("{} MainWindow".format(_('Terminating')))
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
            qDebug(_('Edition not permitted, box locked'))
            return False
        return True

    @Slot()
    def tableQuestionsChanged(self,resetExam=True):
        if self.debug:
            qDebug('{}'.format(_('Questions changed')))
        if resetExam:
            self.currentExam = None
        data = self.tableQuestions.getCellContent(named=True)
        self.scroll.syncMapTableData(data)

    @Slot(int)
    def editingQuestion(self, row):
        qDebug("{} {}".format(_('Editing'),row))
        self.editing_question = row

    @Slot(int)
    def questionChanged(self,row=None):
        if row is not None and self.editing_question == row:
            self.editing_question = None
            qDebug("{} {}".format(_('Question changed'),row))
            self.tableQuestionsChanged()

    @Slot(str,str)
    def updateTitleRow(self,row_uuid,content):
        # qDebug("Updating title col")
        self.tableQuestions.updateTitleRow(row_uuid,content)

    def initializePrinting(self):
        if not self.sheet:
            self.sheet = helperPDF(parent=self,debug=self.debug)
        examData = self.buildExamData()
        config = examData.get('config')
        exam = None
        if self.currentExam:
            exam = self.currentExam
        else:
            exam = examData.get('examdata')
            if config:
                alter = config.get('alter')
                nmodels = config.get('nmodels')
                if exam:
                    if self.debug:
                        qDebug('{}'.format(_('Generating new mix')))
                    exam = self.mixData(exam,nmodels,alter)
        self.currentExam = exam
        header = examData.get('header')
        if header:
            self.sheet.setHeaderInfo(header)
        if exam:
            self.sheet.setExamData(exam)

    def swapOptionElements(self,op1,op2):
        keys = ['text2','pic2','pic2_name']
        for x in keys:
            tmp = op1[x]
            op1[x] = op2[x]
            op2[x] = tmp

    def reorderJoinOptions(self, oplist):
        newList = deepcopy(oplist)
        mapping = [ None ] * len(oplist)
        available = set( range(len(newList)) )
        while len(available):
            i = choice(list(available))
            r = choice(list(available))
            if r != i:
                self.swapOptionElements(newList[i],newList[r])
                available.remove(r)
                available.remove(i)
                mapping[i] = r
                mapping[r] = i
            else:
                available.remove(i)
                mapping[i] = i
        return newList, mapping

    def unSwapOptionElements(self,oplist,mapping):
        i = -1
        used = set()
        for m in mapping:
            i += 1
            if i in used:
                continue
            used.add(i)
            if m == i:
                continue
            used.add(m)
            self.swapOptionElements(oplist[i],oplist[m])

    def getRandomCandidate(self,candidates,notprefer=[]):
        maxiter = 5
        if not isinstance(notprefer,list):
            notprefer = [notprefer]
        s = len(candidates)-1
        for i in range(maxiter):
            seed(urandom(8))
            j = randint(0,s)
            c = candidates[j]
            if c not in notprefer:
                return c
            elif i == maxiter-1:
                return c

    def reorderQuestionOptions(self, oplist):
        oplistcopy = deepcopy(oplist)
        newList = []
        mapping = []
        while len(oplistcopy):
            seed(urandom(8))
            pos = randint(0,len(oplistcopy)-1)
            newList.append(oplistcopy.pop(pos))
        for o in newList:
            mapping.append(int(o.get('order'))-1)
        return newList,mapping

    def mixData(self, examdata, nmodels=1, alter=False):
        # mix join options
        for order,data in enumerate(examdata):
            if data.get('type') == 'join_activity':
                newdata, jmapping = self.reorderJoinOptions(data['options'])
                data['options'] = newdata
                data['join_mapping'] = jmapping

        fixed = sorted([ nquestion for nquestion,questiondata in enumerate(examdata) if questiondata.get('fixed') ])
        linked = sorted([ nquestion for nquestion,questiondata in enumerate(examdata) if questiondata.get('linked') ])
        linked_groups = []
        group = []
        for i in range(len(examdata)):
            if i in linked:
                group.append(i)
            else:
                if len(group):
                    linked_groups.append(group)
                    group = []
            if i == len(examdata)-1:
                if len(group):
                    linked_groups.append(group)

        mapping = {}
        for i in range(nmodels):
            examdatacopy = deepcopy(examdata)
            modelname = chr(65+i).upper()
            mapping.setdefault(modelname,[{}]*len(examdatacopy))
            newOrder = [{None:None}]*len(examdatacopy)
            # put fixed elements
            j = -1
            used = []
            while j < len(examdatacopy):
                j += 1
                if j in fixed:
                    mapping[modelname][j]=examdatacopy[j]
                    used.append(j)
                    if j in linked:
                        group = [ g for g in linked_groups if j in g ][0]
                        if group[0] != j:
                            raise ValueError()
                        for g in group[1:]:
                            if g != j+1:
                                raise ValueError()
                            mapping[modelname][g]=examdatacopy[g]
                            used.append(g)
                            j += 1

            # put linked and not fixed
            pending = [ x for x in range(len(examdata)) if not mapping[modelname][x] ]
            for g in linked_groups:
                size = len(g)
                if not size:
                    raise ValueError()
                if g[0] in used:
                    continue
                available_holes = []
                for p in pending:
                    found = True
                    for j in range(p,size+p):
                        if j not in pending:
                            found = False
                            break
                    if found:
                        available_holes.append(p)
                if not len(available_holes):
                    raise ValueError()
                candidate = self.getRandomCandidate(available_holes,[g[0]])
                group_pos = g[0]
                for j in range(len(g)):
                    if mapping[modelname][candidate+j]:
                        raise ValueError()
                    mapping[modelname][candidate+j] = examdatacopy[group_pos+j]
                    used.append(group_pos+j)
                    if candidate+j in available_holes:
                        available_holes.remove(candidate+j)
                    pending.remove(group_pos+j)

            # simple elements
            available_holes = [ x for x in range(len(examdatacopy)) if not mapping[modelname][x] ]
            while len(pending):
                p = pending[0]
                candidate = self.getRandomCandidate(available_holes,[p])
                if mapping[modelname][candidate]:
                    raise ValueError()
                mapping[modelname][candidate] = examdata[p]
                used.append(p)
                available_holes.remove(candidate)
                pending.remove(p)

            # reorder options into questions
            if alter:
                for order,data in enumerate(mapping[modelname]):
                    options = data.get('options')
                    join_mapping = None
                    # debug_op = deepcopy(options)
                    if options:
                        join_mapping = data.get('join_mapping')
                        if join_mapping:
                            self.unSwapOptionElements(options,join_mapping)
                            newdata, jmapping = self.reorderJoinOptions(options)
                            data['options'] = newdata
                            options = newdata
                            data['join_mapping'] = jmapping
                        newOptions,omapping = self.reorderQuestionOptions(options)
                        data['option_mapping'] = omapping
                        data['options'] = newOptions
        return mapping

    @Slot(int)
    def clickedPreview(self,checked):   
        # qDebug("Preview clicked!")
        self.initializePrinting()
        self.sheet.openWidget(answermode=False)
        if self.with_solutionary:
            self.sheet.openWidget(answermode=True)

    def print_exam(self, filename=None):
        self.initializePrinting()
        if self.with_solutionary:
            filename2 = os.path.splitext(filename)
            filename2 = filename2[0]+'_'+_('solution')+filename2[1]
        if os.path.exists(filename2):
            ret = self.MakeDialog('question',"{} «{}» {}!\n {}".format(_('The file'),filename2,_('already exists'),_('are you sure to overwrite it?')), bigtext=False)
            if not ret:
                return
        self.sheet.writePDF(filename,answermode=False)
        if self.with_solutionary:
            self.sheet.writePDF(filename2,answermode=True)

    def loadUi(self):
        # Removed ! now using uic
        #
        # global UI
        # ui_file = QFile(UI)
        # ui_file.open(QFile.ReadOnly)
        # ui_loader = QUiLoader(self)
        # window = ui_loader.load(ui_file)
        # ui_file.close()
        window = MainWindow()
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
            action = Helper.genAction(name=q.getTranslatedName(),fn=self.menuController,data=q.getNameId(),icon=QIcon(ICONS[iconname]),tip=q.getTranslatedName(),parent=self)
            self.window.toolBar.addAction(action)
        if self.debug_translations:
            action = Helper.genAction(name=_('Print Qt translations'),fn=self.translator.printAcumulatedPythonStrings,icon=QIcon(ICONS['print']),tip=_('Print Qt translations'),parent=self)
            self.window.toolBar.addAction(action)

    def openfiledialog(self):
        f = QFileDialog().getOpenFileName(None,_("Open Exam"),expanduser("~"),"{} (*.kmt)".format(_('Exam files')))
        return f[0] if f else None

    def savefiledialog(self):
        f = QFileDialog.getSaveFileName(None,_("Save Exam"),expanduser("~"),"{} (*.kmt)".format(_('Exam files')))
        return f[0] if f else None

    def openOutputFilenamedialog(self):
        f = QFileDialog.getSaveFileName(None,'{} PDF'.format(_("Export to")),expanduser("~"),"{} (*.pdf)".format(_('Document files')))
        return f[0] if f else None

    def buildExamData(self, template=False):
        e = {
            'version': 1,
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
            self.tableQuestionsChanged(resetExam=False)
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
        if self.dialogheader:
            data = self.dialogheader.dumpData()
        return data

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

    def loadHeader(self,headerdata):
        if not self.dialogheader:
            self.dialogheader = HeaderController(parent=self.window)
        if not self.dialogheader.loadData(headerdata):
            self.window.statusbar.showMessage("{}".format(_('Fail to load header data')),10*1000)

    def generateHeaderMenu2(self):
        if not self.dialogheader:
            self.dialogheader = HeaderController(parent=self.window)
        self.dialogheader.show()

    def generateMixMenu(self):
        def updateValues(dialog):
                le = dialog.findChild(QLineEdit,'n_models')
                c = dialog.findChild(QCheckBox,'alter_models')
                c2 = dialog.findChild(QCheckBox,'with_solutionary')
                self.n_models = int(le.text())
                self.alter_models = c.checkState() == Qt.CheckState.Checked
                self.with_solutionary = c2.checkState() == Qt.CheckState.Checked
                dialog.close()

        dialog = QDialog(self.window,Qt.Window)
        dialog.setModal(True)
        dialog.setWindowTitle(_('Generate mix'))
        dialog.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        l1 = QLabel("{}:".format(_('Number disctinct models')),parent=dialog)
        le = QLineEdit()
        le.setObjectName('n_models')
        le.setMaxLength(1)
        le.setFixedWidth(le.sizeHint().height())
        le.setInputMask("D")
        le.setText(str(self.n_models))
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(l1)
        hlayout1.addWidget(le)
        
        l2 = QLabel("{}:".format(_('Alter answer order')),parent=dialog)
        c = QCheckBox(parent=dialog)
        c.setObjectName('alter_models')
        state = Qt.Unchecked
        if self.alter_models:
            state = Qt.Checked
        c.setCheckState(state)
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(l2)
        hlayout2.addWidget(c,0,Qt.AlignRight)

        l3 = QLabel("{}:".format(_('Include solutionary')),parent=dialog)
        c2 = QCheckBox(parent=dialog)
        c2.setObjectName('with_solutionary')
        state = Qt.Unchecked
        if self.with_solutionary:
            state = Qt.Checked
        c2.setCheckState(state)
        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(l3)
        hlayout3.addWidget(c2,0,Qt.AlignRight)

        hlayout4 = QHBoxLayout()
        b1 = QPushButton(_('Ok'))
        b2 = QPushButton(_('Close'))
        b1.setCheckable(False)
        b1.clicked.connect(lambda: updateValues(dialog))
        b2.setCheckable(False)
        b2.clicked.connect(lambda: dialog.close())
        hlayout4.addWidget(b1,0,Qt.AlignRight)
        hlayout4.addWidget(b2,0,Qt.AlignRight)
        
        w1 = QWidget(parent=dialog)
        w2 = QWidget(parent=dialog)
        w3 = QWidget(parent=dialog)
        w4 = QWidget(parent=dialog)

        w1.setLayout(hlayout1)
        w2.setLayout(hlayout2)
        w3.setLayout(hlayout3)
        w4.setLayout(hlayout4)

        vlayout.addWidget(w1)
        vlayout.addWidget(w2)
        vlayout.addWidget(w3)
        vlayout.addWidget(w4,0,Qt.AlignRight)
        
        dialog.exec()

    def MakeDialog(self, typeq, message , informative="", bigtext=True):
        dialog = QMessageBox()
        message = "\n"+message
        hspacer = QSpacerItem(300,0,QSizePolicy.Minimum,QSizePolicy.Expanding)
        if bigtext:
            size = 12
        else:
            size = 10
        if typeq == 'info':
            dialog.setProperty('icon',QMessageBox.Information)
            dialog.setStandardButtons(QMessageBox.Ok)
        elif typeq == 'question':
            dialog.setProperty('icon',QMessageBox.Question)
            dialog.setStandardButtons(QMessageBox.Ok|QMessageBox.No)
        dialog.setText("{}".format(message))
        if informative:
            dialog.setInformativeText(informative)
        dialog.setStyleSheet('QMessageBox QLabel#qt_msgbox_label{{ font-size: {}pt; }} QMessageBox QLabel#qt_msgbox_informativelabel{{ font-size: {}pt; }}'.format(size,size-2))
        dialog.layout().addItem(hspacer,dialog.layout().rowCount(),0,1,dialog.layout().columnCount())
        ret = dialog.exec_()
        if typeq == 'question':
            if ret == QMessageBox.Ok:
                return True
            else:
                return False
        return ret

    @Slot(str)
    def menuController(self,*args,**kwargs):
        if self.debug:
            qDebug('{} menuController'.format(_('Called')))
        if not args:
            if self.sender():
                data = self.sender().data()
            else:
                raise ValueError()
        else:
            data = args[0]
        if not data:
            raise ValueError()
        if self.debug:
            qDebug('{} "{}" click'.format(_('Menu'),data))
        if data == 'menu_exit_app':
            self.exitting()
        elif data == 'menu_load_exam':
            if self.autoloadfilename:
                filename = self.autoloadfilename
                self.autoloadfilename = None
            else:
                filename = self.openfiledialog()
            if filename:
                self.tableQuestions.clearTable()
                examData = self.persistence.loadExam(filename)
                version = examData.get('version')
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
            self.header_data = None
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
            self.currentExam = None
            self.window.statusbar.showMessage("{}: {}".format(_('New question'),data),10*1000)
            q = Question().search(data)
            self.tableQuestions.addItem(q.getName())
        elif data == 'menu_print_exam':
            self.output_filename = self.openOutputFilenamedialog()
            if self.output_filename:
                self.print_exam(self.output_filename)
        elif data == 'menu_generate_mix':
            self.currentExam = None
            self.MakeDialog('info', _('New mix will be generated'))
        elif data == 'menu_configure_output':
            self.generateMixMenu()
        elif data == 'menu_configure_header':
            self.generateHeaderMenu2()
            # self.generateHeaderMenu()
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
            qDebug("{} '{}' menuaction".format(_('No action declared for'),data))
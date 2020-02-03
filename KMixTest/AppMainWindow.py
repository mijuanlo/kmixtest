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

from os.path import expanduser

# Main class of application
class AppMainWindow(QApplication):    
    def __init__(self):
        super().__init__([])
        try:
            self.window = self.loadUi()
            self.menu = MenuItem(menu=self.window.menubar,parent=self)
            self.menu.itemActivation.connect(self.menuController)
            #self.window.gridEdition.addItem(QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Expanding))
            self.window.show()
            self.bind_toolbar_actions()
            self.tableQuestions = tableHelper(self.window.tableWidgetQuestions, self)
            self.tableQuestions.editingQuestion.connect(self.editingQuestion)
            self.window.scrollAreaAnswers.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )

            self.scroll = gridHelper(self.window.gridEdition, self)
            self.window.previewButton.clicked.connect(self.clickedPreview)
            self.window.previewButton.hide()
            self.tableQuestions.rowSelection.connect(self.scroll.showQuestion)
            self.sheet = None
            self.aboutToQuit.connect(self.exitting)
            self.persistence = Persistence(debug=True)
            self.menu.addMenuItem([{"Project":["New|new","-","Load Exam","-","Save|save","Save as|save","-","Exit|exit"]},{"Mixer":["Configure header","Generate Mix"]},{"Print":["Print preview|print","Print Exam|print"]}])
            self.tableQuestions.pool.start_threads()
        except Exception as e:
            print("Exception when initializing, {}".format(e))
            self.exitting()
    @Slot()
    def exitting(self):
        global NATIVE_THREADS
        qDebug("Exitting")
        if self.tableQuestions:
            if self.tableQuestions.pool:
                self.tableQuestions.pool.terminate = True
                self.tableQuestions.pool.abort()
                if NATIVE_THREADS:
                    self.tableQuestions.pool.threadpool.clear()
        self.quit()

    @Slot(int)
    def editingQuestion(self, row):
        qDebug("Editing {}".format(row))

    @Slot(bool)
    def clickedPreview(self,checked):
        qDebug("Preview clicked!")
        if not self.sheet:
            self.sheet = helperPDF(parent=self)
        self.sheet.openWidget()

    def loadUi(self):
        global UI
        ui_file = QFile(UI)
        ui_file.open(QFile.ReadOnly)
        ui_loader = QUiLoader(self)
        window = ui_loader.load(ui_file)
        ui_file.close()
        return window

    def bind_toolbar_actions(self):
        for action in dir(self.window):
            action_obj = getattr(self.window,action)
            if isinstance(action_obj,QAction):
                action_obj.setData(action_obj.text())
                action_obj.triggered.connect(self.newQuestion)

    @Slot()
    def newQuestion(self):
        if self.sender():
            data = self.sender().data()
        else:
            raise ValueError("No sender detected")
        qDebug("senderData:{}".format(data))
        self.window.statusbar.showMessage("Action from '{}' triggered".format(data),10*1000)
        self.tableQuestions.addItem(data)

    def openfiledialog(self):
        f = QFileDialog().getOpenFileName(None,self.tr("Open Exam"),expanduser("~"),self.tr("Exam files (*.kmt)"))
        return f[0] if f else None

    def savefiledialog(self):
        f = QFileDialog().getSaveFileName(None,self.tr("Save Exam"),expanduser("~"),self.tr("Exam files (*.kmt)"))
        return f[0] if f else None

    def buildExamData(self):
        model = self.tableQuestions.dumpTableModel()
        i = 0
        for row in model:
            row.insert(0,i)
            i+=1
        return model

    def useExamData(self,examData):
        model = {}
        if not examData:
            raise ValueError()
        for row in examData:
            model.setdefault(row[0],(row[3],(row[1],row[2])))
        for x in sorted(model.keys()):
            name, states = model.get(x)
            fixed,linked = states
            self.tableQuestions.addItemWithState(name,bool(fixed),bool(linked))
        return None

    @Slot(str)
    def menuController(self,*args,**kwargs):
        if not args:
            return
        data = args[0]
        print('Menu "{}" click'.format(data))
        if data == 'Exit':
            self.exitting()
        elif data == 'Load':
            filename = self.openfiledialog()
            if filename:
                self.tableQuestions.clearTable()
                self.persistence.newExam()
                examData = self.persistence.loadExam(filename)
                self.useExamData(examData)
        elif data == 'New':
            self.tableQuestions.clearTable()
            self.persistence.newExam()
        elif data == 'Save as':
            filename = self.savefiledialog()
            if filename:
                examData = self.buildExamData()
                result = self.persistence.saveExam(filename,examData)
        elif data == 'Print Exam':
            self.clickedPreview(True)
        else:
            qDebug("No action declared for '{}' menuaction".format(data))


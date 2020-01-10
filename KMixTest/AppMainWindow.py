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

# Main class of application
class AppMainWindow(QApplication):
    def __init__(self):
        super().__init__([])
        self.menu = {}
        self.window = self.loadUi()
        self.window.show()
        self.addMenuItem(["one","two"],["some","other",["menuitem"]])
        self.bind_toolbar_actions()
        self.tableQuestions = tableHelper(self.window.tableWidgetQuestions, self)
        self.tableQuestions.editingQuestion.connect(self.editingQuestion)
        self.window.scrollAreaAnswers.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
        self.scroll = gridHelper(self.window.gridEdition, self)
        self.window.previewButton.clicked.connect(self.clickedPreview)
        self.tableQuestions.rowSelection.connect(self.scroll.showQuestion)
        self.sheet = None
        self.aboutToQuit.connect(self.exitting)
        self.persistence = Persistence()

    @Slot()
    def exitting(self):
        global NATIVE_THREADS
        qDebug("Exitting")
        self.tableQuestions.pool.terminate = True
        self.tableQuestions.pool.abort()
        if NATIVE_THREADS:
            self.tableQuestions.pool.threadpool.clear()
        #exit(0)
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
                action_obj.triggered.connect(self.test)

    @Slot()
    def test(self):
        data = self.sender().data()
        qDebug("senderData:{}".format(data))
        self.window.statusbar.showMessage("Action from '{}' triggered".format(data),10*1000)
        self.tableQuestions.addItem(data)
        pass

    def calculate_default_menubar_shortcut(self,name):
        used = []
        for item in self.menu:
            for character in item:
                if character in used:
                    continue
                else:
                    used.append(character)
                    break
        newname = ""
        done = False
        for character in name:
            if done or character in used:
                newname += character
            else:
                newname += "&" + character
                done = True

        return newname

    def addMenuItem(self, *args, **kwargs):
        for name in args:
            if isinstance(name,list):
                self.addMenuItem(*name)
                continue
            if not isinstance(name,str) or name in self.menu:
                continue
            name_with_shortcut = self.calculate_default_menubar_shortcut(name)
            self.menu.setdefault(name,[])
            self.menu[name].append(self.window.menubar.addMenu(name_with_shortcut))
            action = Helper.genAction(name=name,fn=self.test,icon=ICONS['option'],tip=name,parent=self.menu[name][0],data=name)
            self.menu[name][0].addAction(action)

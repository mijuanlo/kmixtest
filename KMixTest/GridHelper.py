from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Box import Box

# Class with helper to manage grid content used for question contents
class gridHelper(QObject):
    def __init__(self, grid=None, parent=None):
        super().__init__()
        self.parent = parent
        self.grid = grid
        self.boxes = {}
        self.orderedBoxes = {}
        self.idbox = 0
        #self.init(self.grid)

    def init(self, grid):
        self.addToGrid(self.toolbar)
        self.action = QAction("COSA")
        self.toolbar.addAction(self.action)
        self.toolbar1 = QMenuBar(self.parent.window.scrollAreaContentsAnswers)
        self.addToGrid(self.toolbar1)
        self.action1 = QAction("COSA2")
        self.toolbar1.addAction(self.action1)
        return
        for i in range(5):
            self.idbox += 1
            b = Box("Frame #{}".format(self.idbox))
            self.addToGrid(b)
            b.closedBox.connect(self.closeBox)
            self.boxes.setdefault(b.getId(),b)
            self.addTitleEditor(b.getGrid())
        self.spacer = QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Expanding)
        self.addToGrid(self.spacer)

    def printGridInformation(self):
        gridData = self.getGridData()
        for y in range(len(gridData)):
            row = gridData[y]
            rowstr=[]
            is_empty = True
            for x in range(len(row)):
                i = row[x]
                if i:
                    rowstr.append('{}:{}'.format(x,str(i)))
                    is_empty = False
                else:
                    rowstr.append('{}:<empty>'.format(x))
            if not is_empty:
                qDebug('Row: {} -> {}'.format(y,','.join(rowstr)))

    def getTableData(self):
        data = []
        table = self.parent.tableQuestions
        model = table.model
        for y in range(model.rowCount()):
            row = []
            for x in range(model.columnCount()):
                d = model.data(model.index(y,x),Qt.DisplayRole)
                if not d:
                    d = model.data(model.index(y,x),Qt.UserRole)
                row.append(d)
            data.append(row)
        return data
    
    def getGridData(self):
        gridData=[]
        for y in range(self.grid.rowCount()):
            rowData = []
            for x in range(self.grid.columnCount()):
                i = self.grid.itemAtPosition(y,x)
                rowData.append(i)
            gridData.append(rowData)
        return gridData
    
    def reorderGrid(self):
        ordered = {}
        typeRemove=(Box)
        hide = False
        if not len(self.boxes):
            hide = True
        for b in self.boxes:
            ordered.setdefault('{}{}'.format(self.boxes[b].getData()[0][0],b),self.boxes[b])
        toRemove = []
        for j in range(self.grid.count()):
            item = self.grid.itemAt(j).widget()
            if isinstance(item,typeRemove):
                toRemove.append(j)
            else:
                if hide:
                    item.hide()
                else:
                    item.show()
        while toRemove:
            self.grid.takeAt(toRemove.pop())
        for w in sorted(ordered):
            self.addToGrid(ordered[w])
        self.grid.update()

    Slot(int)
    def showQuestion(self, row):
        qDebug("Showing question {}".format(row))
        data = self.getTableData()
        datarow = data[row]
        b = Box("{}".format(datarow[3]))
        b.setData(datarow[3:])
        self.addToGrid(b)
        b.closedBox.connect(self.closeBox)
        self.boxes.setdefault(b.getId(),b)
        self.addTitleEditor(b.getGrid())
        #self.spacer = QSpacerItem(0,0,QSizePolicy.Fixed,QSizePolicy.Expanding)
        #self.addToGrid(self.grid,self.spacer)
        self.reorderGrid()
        self.printGridInformation()

    Slot(str)
    def closeBox(self, uuid):
        qDebug("Closing {}".format(uuid))
        b = self.boxes.get(uuid,None)
        if b:
            del self.boxes[uuid]
            self.grid.removeWidget(b)
            b.deleteLater()
            #if len(self.boxes) == 0:
            #    self.grid.removeItem(self.spacer)
            #    self.init(self.grid)
            self.grid.update()
        self.reorderGrid()
        self.printGridInformation()

    def addToGrid(self, what ,on=None, x=None, y=None ):
        if not what:
            raise ValueError
        if not on:
            on = self.grid
        if y is None:
            y = on.rowCount()
        if x is None:
            for i in range(on.columnCount()):
                if on.itemAtPosition(y,i) is None:
                    x = i
                    break

        if isinstance(what,QWidget):
            on.addWidget(what,y,x)
            return
        if isinstance(what,QLayoutItem):
            on.addItem(what,y,x)
            return
        if isinstance(what,list):
            all_widget = True
            all_list = True
            for i in what:
                if not isinstance(i,QWidget):
                    all_widget = False
                if not isinstance(i,list):
                    all_list = False
            if all_widget:
                for i in what:
                    self.addToGrid(i,on)
            if all_list:
                all_widget = True
                for i in what:
                    for j in i:
                        if not isinstance(j,QWidget):
                            all_widget = False
                            break
                    if not all_widget:
                        break
                if not all_widget:
                    qDebug("Error")
                    return
                else:
                    offset_x=0
                    for i in what:
                        for j in i:
                            self.addToGrid(j,on,x+offset_x,y)
                            offset_x+=1
        return

    def addTitleEditor(self, on):
        label = QLabel("Title")
        textedit = QTextEdit()
        self.addToGrid([[label,textedit]],on)
 
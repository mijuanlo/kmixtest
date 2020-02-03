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
        self.tableDataMap = {}
        self.orderedBoxes = {}
        self.idbox = 0
        #self.init(self.grid)

    def init(self, grid):
        pass

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

    def updatedTableData(self):
        self.getTableData()

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
        self.syncMapTableData(data)
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
    
    # def reorderGrid(self):
    #     ordered = {}
    #     typeRemove=(Box)
    #     hide = False
    #     if not len(self.boxes):
    #         hide = True
    #     for b in self.boxes:
    #         ordered.setdefault('{}{}'.format(self.boxes[b].getData()[0][0],b),self.boxes[b])
    #     toRemove = []
    #     for j in range(self.grid.count()):
    #         item = self.grid.itemAt(j).widget()
    #         if isinstance(item,typeRemove):
    #             toRemove.append(j)
    #         else:
    #             if hide:
    #                 item.hide()
    #             else:
    #                 item.show()
    #     while toRemove:
    #         self.grid.takeAt(toRemove.pop())
    #     for w in sorted(ordered):
    #         self.addToGrid(ordered[w])
    #     self.grid.update()

    def hide_all_boxes(self):
        for x in self.boxes:
            self.boxes.get(x).hide()

    def syncMapTableData(self,data):
        ids = []
        for x in data:
            id_row = x[4]
            self.tableDataMap.setdefault(id_row,None)
            ids.append(id_row)
        toRemove=[]
        for x in self.tableDataMap:
            if x not in ids:
                toRemove.append(x)
        for x in toRemove:
            box_uuid = self.tableDataMap.get(x)
            self.deleteBox(box_uuid)
            del self.tableDataMap[x]

    Slot(int)
    def showQuestion(self, row):
        data = self.getTableData()
        datarow = data[row]
        name_from_row = datarow[3]
        id_from_row = datarow[4]
        self.hide_all_boxes()
        id_box = self.tableDataMap.get(id_from_row)
        if id_box:
            qDebug("Showing question {}".format(row))
            self.boxes.get(id_box).show()
        else:
            qDebug("Showing question {} (new)".format(row))
            b = Box("{}".format(name_from_row))
            b.menu.itemActivation.connect(self.parent.menuController)
            b.setData(name_from_row,id_from_row)
            id_box = b.getId()
            self.tableDataMap[id_from_row] = id_box
            self.addToGrid(b)
            b.closedBox.connect(self.closeBox)
            self.boxes.setdefault(id_box,b)
            self.addTitleEditor(b.getGrid(),name_from_row)
        #self.reorderGrid()
        self.printGridInformation()

    def deleteBox(self,uuid):
        if not uuid:
            raise ValueError()
        qDebug("Deleting {}".format(uuid))
        b = self.boxes.get(uuid,None)
        if b:
            del self.boxes[uuid]
            self.grid.removeWidget(b)
            b.deleteLater()
            self.grid.update()
        #self.reorderGrid()
        self.printGridInformation()

    Slot(str)
    def closeBox(self, uuid):
        if not uuid:
            raise ValueError()
        qDebug("Closing {}".format(uuid))
        b = self.boxes.get(uuid,None)
        if b:
            b.hide()
            self.grid.update()
        #self.reorderGrid()
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

    def addTitleEditor(self, on=None, content=None ):
        if not on:
            raise ValueError()
        label = QLabel("Title")
        if content:
            textedit = QTextEdit(content)
        else:
            textedit = QTextEdit()
        self.addToGrid([[label,textedit]],on)
 
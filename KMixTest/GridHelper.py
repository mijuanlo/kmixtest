from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Box import Box
from .QuestionType import Question

# Class with helper to manage grid content used for question contents
class gridHelper(QObject):

    boxIsUpdating = Signal(str,str)

    def __init__(self, grid=None, parent=None):
        super().__init__()
        self.parent = parent
        self.grid = grid
        # Links box_uuid with object
        self.boxes = {}
        # Links row_uuid with box_uuid
        self.tableDataMap = {}
        # Links box_uuid with row_uuid
        self.tableDataMapReversed = {}
        self.orderedBoxes = {}
        self.idbox = 0
        self.last_tabledata = None

    def getBoxFromRowId(self,row_uuid):
        box_uuid = self.tableDataMap.get(row_uuid)
        if not box_uuid:
            return None
        return self.boxes.get(box_uuid)

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
    
    def getGridData(self):
        gridData=[]
        for y in range(self.grid.rowCount()):
            rowData = []
            for x in range(self.grid.columnCount()):
                i = self.grid.itemAtPosition(y,x)
                rowData.append(i)
            gridData.append(rowData)
        return gridData

    def hide_all_boxes(self):
        for x in self.boxes:
            self.boxes.get(x).hide()

    def syncMapTableData(self,data=None):
        if data is not None:
            self.last_tabledata = data
        else:
            raise ValueError()
        #qDebug("Syncing table-grid data")
        ids = []
        for x in data:
            id_row = x.get('_UUID_')
            self.tableDataMap.setdefault(id_row,None)
            ids.append(id_row)
        toRemove=[]
        for x in self.tableDataMap:
            if x not in ids:
                toRemove.append(x)
        for x in toRemove:
            box_uuid = self.tableDataMap.get(x)
            if box_uuid:
                self.deleteBox(box_uuid)
            del self.tableDataMap[x]
        self.tableDataMapReversed = { v:k for k,v in self.tableDataMap.items() }
        # update title
        for x in data:
            title = x.get('title')
            if not title:
                raise ValueError()
            id_row = x.get('_UUID_')
            box_id = self.tableDataMap[id_row]
            if box_id:
                box = self.boxes.get(box_id)
                box.updateTitle(title)

    def createBox(self, typeq, rowuid, title=None):
        q = Question()
        if typeq not in q.allTypes():
            raise ValueError()

        b = Box()
        b.setData('type',typeq)
        
        content = ''
        if title:
            content = '{} with type {}'.format(title,typeq)
        b.setData('initial_content',content)

        b.closedBox.connect(self.closeBox)
        b.contentChanged.connect(self.boxChanged)

        id_box = b.getId()
        self.tableDataMap[rowuid] = id_box
        self.tableDataMapReversed[id_box] = rowuid
        self.boxes.setdefault(id_box,b)
        
        b.makeQuestionTypeLayout()
        self.addToGrid(b)

        return b

    def loadBox(self,boxData):
        def check(d,needed):
            keys = d.keys()
            for x in needed:
                if x not in keys:
                    raise ValueError()
                if not boxData.get(x):
                    raise ValueError()
        if not isinstance(boxData,dict):
            raise ValueError()

        needed = ['uuid','type']
        check(boxData,needed)
        
        typeq = boxData.get('type')
        b = self.createBox(boxData.get('type'),boxData.get('uuid'),boxData.get('title'))
        # COMMON FIELDS
        title_pic = boxData.get('title_pic')
        title_filename = boxData.get('title_picname')
        locked = boxData.get('locked')
        if title_pic:
            b.addImageToTitle(title_filename,title_pic)
        if locked:
            b.lock = True
        # TYPED FIELDS
        if typeq == 'single_question':
            needed = ['empty_lines']
            check(boxData,needed)
            b.setSliderValue(boxData.get('empty_lines'))
        elif typeq in ['test_question','join_activity']:
            options = boxData.get('options')
            opt_map = {}
            i = 0
            for option in options:
                nop = option.get('order')
                if not nop:
                    raise ValueError()
                opt_map.setdefault(str(nop),i)
                i += 1
            for nop in sorted(opt_map.keys()):
                option = options[opt_map.get(nop)]
                if typeq == 'test_question':
                    b.loadOptionTest(option)
                else:
                    b.loadJoinOption(option)
            if typeq == 'test_question':
                needed = ['nvalid']
                check(boxData,needed)
                b.configureSlider(1,len(options),boxData.get('nvalid'))
        else:
            qDebug('Can\'t load type {}'.format(typeq))
        b.do_lock()

    @Slot(int)
    def showQuestion(self, row):
        data = self.last_tabledata
        datarow = data[row]
        name_from_row = datarow['title']
        id_from_row = datarow['_UUID_']
        type_from_row = datarow['_TYPE_']
        self.hide_all_boxes()
        id_box = self.tableDataMap.get(id_from_row)
        if id_box:
            qDebug("Showing question {}".format(row))
            self.boxes.get(id_box).show()
        else:
            qDebug("Showing question {} (new)".format(row))
            b = self.createBox(type_from_row,id_from_row,name_from_row)
            #self.addToGrid(b)
            #b.makeQuestionTypeLayout()
        self.printGridInformation()

    @Slot(str,str)
    def boxChanged(self,box_uuid,content):
        row_uuid = self.tableDataMapReversed.get(box_uuid)
        if not row_uuid:
            raise ValueError()
        self.boxIsUpdating.emit(row_uuid,content)

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
        self.printGridInformation()

    def dumpBoxes(self):
        boxdata = {}
        for rowid,boxid in self.tableDataMap.items():
            box = self.boxes.get(boxid)
            boxInfo = None
            if box:
                boxInfo = box.dumpBox()
            boxdata.setdefault(rowid,boxInfo)
        return boxdata

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

 
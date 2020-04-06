from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Ui_headerForm import Ui_headerForm
from .Util import dumpPixMapData, loadPixMapData, fileToPixMap

from os.path import expanduser
from copy import deepcopy

class HeaderController(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__()
        parent = kwargs.get('parent')
        self._parent = None
        if parent:
            self._parent = parent
            self.setWindowTitle("{} {}".format(self._parent.windowTitle(),_('header designer')))
        self.ui = Ui_headerForm()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        self.reset()
        self.makeConnections()
        self.initUI()

    @Slot(int)
    def closeEvent(self, *args):
        self.loadData(self.backupData)
        self.hide()
        return True

    def dumpData(self):
        data = None
        data = { 
            'ncols': self.ncols,
            'nrows': self.nrows,
            'joins': self.tjoins,
            'content': self.tcontent
        }
        return deepcopy(data)

    def checkRange(self, value, minv, maxv):
        if isinstance(value,str):
            if value.isnumeric():
                value = int(value)
        for p in [value,minv,maxv]:
            if not isinstance(p,int):
                return False
        if value not in range(minv,maxv+1):
            return False
        return True

    def checkKeyIntegrity(self, key):
        if not isinstance(key,str):
            return False
        l = key.split('_')
        if not l or len(l) != 2:
            return False
        y,x = l
        if not self.checkRange(y,0,self.max_nrows):
            return False
        if not self.checkRange(x,0,self.max_ncols):
            return False
        return True

    def checkDataIntegrity(self, data):
        if not isinstance(data,dict):
            return False
        for k in ['ncols','nrows','joins','content']:
            if k not in data.keys():
                return False
        for k in ['ncols','nrows']:
            n = data.get(k)
            if k == 'ncols':
                maxv=self.max_ncols
            else:
                maxv=self.max_nrows
            if not self.checkRange(n,1,maxv):
                return False
        for k in ['joins','content']:
            if not isinstance(data.get(k),dict):
                return False
        for k,v in data.get('joins').items():
            if not isinstance(v,(tuple,list)) or len(v) != 2:
                return False
            sy,sx = v
            if not self.checkRange(sy,1,self.max_nrows):
                return False
            if not self.checkRange(sx,1,self.max_ncols):
                return False
            if sx + sy < 3:
                return False
        for k,v in data.get('content').items():
            if not self.checkKeyIntegrity(k):
                return False
            if not isinstance(v,dict):
                return False
            for k in ['pix','txt','align']:
                if k not in v.keys():
                    return False
        return True

    def makeSelection(self, row, col, spanrow=None, spancol=None):
        if isinstance(row,str) and row.isnumeric():
            row = int(row)
        if isinstance(col,str) and col.isnumeric():
            col = int(col)
        if not self.checkRange(row,0,self.max_nrows):
            return None
        if not self.checkRange(col,0,self.max_ncols):
            return None
        single = True
        if spanrow:
            if isinstance(spanrow,str) and spanrow.isnumeric():
                spanrow = int(spanrow)
            if not self.checkRange(spanrow,1,self.max_nrows):
                return None
            single = False
        if spancol:
            if isinstance(spancol,str) and spancol.isnumeric():
                spancol = int(spancol)
            if not self.checkRange(spancol,1,self.max_ncols):
                return None
            single = False
        selection = { 'good': True, 'single': single }
        if single:
            span_x = False
            span_y = False
        else:
            if spanrow == 1:
                span_x = True
                span_y = False
            else:
                span_x = False
                span_y = True
        selection['join_rows'] = span_x
        selection['join_cols'] = span_y
        selection['items'] = []
        selection['items'].append((row,col))
        if not single:
            for i in range(1,spanrow):
                selection['items'].append((row+i,col))
            for j in range(1,spancol):
                selection['items'].append((row,col+j))
        return selection

    def reset(self):
        self.removeWidgetsTable()
        self.max_ncols = 5
        self.max_nrows = 5
        self.ncols = 1
        self.nrows = 1
        self.tcontent = {}
        self.tjoins = {}
        self.backupData = None
        if self.ui:
            self.ui.columnSlider.setMaximum(self.max_ncols)
            self.ui.columnSlider.setMinimum(1)
            self.ui.columnSlider.setValue(self.ncols)
            self.ui.columnSlider.valueChanged.emit(self.ncols)
            self.ui.rowSlider.setMaximum(self.max_nrows)
            self.ui.rowSlider.setMinimum(1)
            self.ui.rowSlider.setValue(self.nrows)
            self.ui.rowSlider.valueChanged.emit(self.nrows)
        self.updateN()

    def loadData(self, data):
        if not self.checkDataIntegrity(data):
            return None
        self.ncols = data.get('ncols')
        self.nrows = data.get('nrows')
        self.ui.columnSlider.setValue(self.ncols)
        self.ui.rowSlider.setValue(self.nrows)
        self.tjoins = deepcopy(data.get('joins'))
        for y,x,sy,sx in [ tuple(k.split('_'))+tuple(v) for k,v in self.tjoins.items() ]:
            self.joinClicked(selection=self.makeSelection(y,x,sy,sx))
        self.tcontent = deepcopy(data.get('content'))
        for y,x,celldata in [ tuple(k.split('_'))+(v,) for k,v in self.tcontent.items() ]:
            self.loadCell(y,x,celldata)
        self.backupData = self.dumpData()
        return True

    def loadCell(self, row, col, celldata):
        sel = self.makeSelection(row,col)
        if celldata.get('pix'):
            self.imageClicked(selection=sel)
        else:
            txt = celldata.get('txt')
            if self.isTextField(txt.get('value')):
                self.textClicked(field=txt.get('value').split('_@[')[1].split(']@_')[0],valuefield=txt.get('show'), selection=sel)
            else:
                self.textClicked(txt=txt.get('show'), selection=sel)
        self.alignItem(selection=sel)

    def adjustImages(self):
        list(map(self.resizeImage,self.getWidgetsTable()))
        self.ui.headerTable.resizeEvent(QResizeEvent(self.ui.headerTable.rect().size(),self.ui.headerTable.rect().size()))

    def resizeEvent(self, *args):
        self.adjustImages()
        return super().resizeEvent(*args)

    def initUI(self):
        self.ui.headerTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ui.headerTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.headerTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.headerTable.viewport().installEventFilter(self)

    def getSingleSelection(self, selection=None):
        if selection:
            sel = selection
        else:
            sel = self.getSelection()
        if not sel:
            self.showInfo(_('No cell selected'))
            return None
        if not sel.get('single'):
            self.showInfo(_('Multiple selection not allowed'))
            return None
        cell = sel.get('items')
        if not cell:
            return None
        cell = cell[0]
        return cell

    def getWidgetsIntoSelection(self, selection=None):
        sel = self.getSelection()
        l = []
        if sel:
            items = sel.get('items')
            if items:
                for i in items:
                    if i:
                        y,x = i
                        w = self.ui.headerTable.cellWidget(y,x)
                        l.append((w,y,x))
        return l

    def getWidgetForSelection(self, selection=None):
        t = self.getSingleSelection(selection)
        if t: 
            y,x = t
        else:
            return None
        w = self.ui.headerTable.cellWidget(y,x)
        return w,y,x

    @Slot()
    def emptyCell(self):
        t = self.getSingleSelection()
        if t:
            y,x = t
            key = self.makeKey(y,x)
            self.tcontent[key] = {'pix':None, 'txt':None, 'align':None}
            self.ui.headerTable.removeCellWidget(y,x)
            for b in [self.ui.textButton,self.ui.imageButton,self.ui.studentNameButton,self.ui.dateButton,self.ui.groupButton]:
                b.setDisabled(False)
            self.ui.emptyButton.setDisabled(True)
            for b in [self.ui.alignCenterButton,self.ui.alignLeftButton,self.ui.alignRightButton]:
                    b.setDisabled(True)
            if self.ui.headerTable.rowSpan(y,x) + self.ui.headerTable.columnSpan(y,x) > 2:
                self.ui.splitButton.setEnabled(True)

    @Slot(int)
    def alignItem(self, selection=None):
        name = None
        if not selection:
            s = self.sender()
            if not s:
                return None
            name = s.objectName()
        t = self.getWidgetForSelection(selection=selection)
        if t:
            w,y,x = t
            key = self.makeKey(y,x)
            align = None
            if selection:
                align = self.tcontent[key].get('align')
                if align:
                    name = align
                else:
                    name = 'center'
            if not w:
                self.showInfo('Nothing to align')
                return None
            for b in [self.ui.alignCenterButton,self.ui.alignLeftButton,self.ui.alignRightButton]:
                b.setEnabled(True)
            if 'left' in name.lower():
                w.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
                self.tcontent[key]['align'] = 'left'
                self.ui.alignLeftButton.setDisabled(True)
            elif 'right' in name.lower():
                w.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.tcontent[key]['align'] = 'right'
                self.ui.alignRightButton.setDisabled(True)
            else:
                w.setAlignment(Qt.AlignCenter)
                self.tcontent[key]['align']= 'center'
                self.ui.alignCenterButton.setDisabled(True)

    def getSelection(self):
        lselection = self.ui.headerTable.selectedIndexes()
        size = len(lselection)
        if not size:
            return
        elif size == 1:
            single = True
        else:
            single = False
        x = None
        y = None
        valid = []
        invalid = []
        join_col = False
        join_row = False
        for i in lselection:
            failed = False
            if x is None:
                x = i.column()
            else:
                c = i.column()
                if x != c:
                    if join_col:
                        failed = True
                    if not failed:
                        join_col = False
                        x = c
                else:
                    join_col = True
            if y is None:
                y = i.row()
            else:
                r = i.row()
                if y != r:
                    if join_row:
                        failed = True
                    if not failed:
                        join_row = False
                        y = r
                else:
                    join_row = True
            if failed:
                invalid.append((r,c))
            else:
                valid.append((y,x))
        
        is_good = True
        if len(valid) != size:
            is_good = False
        if join_col and join_row:
            is_good = False
            join_col = False
            join_row = False
        joining = False
        if join_col:
            ordered = False
            while not ordered:
                if not len(valid):
                    break
                d = { y:x for y,x in valid }
                l = sorted(d.keys())
                ordered = True
                for i in range(l[0],l[-1]+1):
                    if ordered:
                        if i not in l:
                            ordered = False
                            is_good = False
                    else:
                        if i in d:
                            valid.remove((i,d[i]))
                            invalid.append((i,d[i]))
            valid = []
            for i in l:
                valid.append((i,d[i]))
            if len(valid) > 1:
                joining = True
        if join_row:
            ordered = False
            while not ordered:
                if not len(valid):
                    break
                d = { x:y for y,x in valid }
                l = sorted(d.keys())
                ordered = True
                for i in range(l[0],l[-1]+1):
                    if ordered:
                        if i not in l:
                            ordered = False
                            is_good = False
                    else:
                        if i in d:
                            valid.remove((d[i],i))
                            invalid.append((d[i],i))
            valid = []
            for i in l:
                valid.append((d[i],i))
            if len(valid) > 1:
                joining = True
                single = False
            elif len(valid) == 1:
                single = True
        return {'joining':joining,'single':single,'good':is_good,'join_cols':join_col,'join_rows':join_row,'items':valid,'invalid':invalid}

    def getImageUrl(self):
        filename = QFileDialog.getOpenFileUrl(self,_('Open image'),QUrl().fromLocalFile(expanduser('~')),'{} (*.png *.jpg *.gif *.svg)'.format(_('Image Files')))
        filename = filename[0]
        url = filename.toString()
        filename = filename.toLocalFile()
        return url,filename

    @Slot()
    def imageClicked(self, selection=None):
        t = self.getWidgetForSelection(selection)
        if t:
            w,y,x = t
        else:
            return None
        if w:
            self.showInfo(_('Cell not empty'))
            return None
        key = self.makeKey(y,x)
        if selection:
            pix = loadPixMapData(self.tcontent.get(key).get('pix'))
            url = None
            filename = None
        else:
            url, filename = self.getImageUrl()
            if not filename:
                return
            pix = fileToPixMap(filename)
        if not pix:
            qDebug('{} {} {}'.format(_('filename'),filename,_('invalid')))
            return None
        l=QLabel()
        l.setPixmap(pix)
        l.setAlignment(Qt.AlignCenter)
        l.setProperty('_filename_',url)
        pixdata = dumpPixMapData(pix)
        l.setProperty('_data_',pixdata)
        self.tcontent.setdefault(key,{'pix':None, 'txt':None, 'align': 'center'})
        self.tcontent[key]['pix'] = pixdata
        self.ui.headerTable.setCellWidget(y,x,l)
        self.resizeImage(y,x)
        for b in [self.ui.alignLeftButton,self.ui.alignRightButton]:
            b.setEnabled(True)
        self.ui.alignCenterButton.setDisabled(True)
        self.ui.splitButton.setDisabled(True)
        self.ui.emptyButton.setEnabled(True)
        for b in [self.ui.textButton,self.ui.imageButton,self.ui.studentNameButton,self.ui.groupButton,self.ui.dateButton]:
            b.setDisabled(True)

    def isTextField(self, text):
        if not isinstance(text,str):
            return False
        if '_@[' in text and ']@_' in text:
                return True
        return False

    @Slot()
    def textClicked(self, field=None, valuefield=None, txt=None, align=Qt.AlignCenter, selection=None):
        t = self.getWidgetForSelection(selection)
        if t:
            w,y,x = t
        else:
            return None
        key = self.makeKey(y,x)
        text = None
        if w:
            if self.tcontent[key]['txt'] and isinstance(self.tcontent[key]['txt'],str) and not self.isTextField(self.tcontent[key]['txt']):
                text = self.tcontent[key]['txt']
            elif self.tcontent[key]['txt'] and not self.isTextField(self.tcontent[key]['txt']['value']):
                text = self.tcontent[key]['txt']['value']
            else:
                self.showInfo(_('Cell not empty'))
                return None
        if text:
            l=w
        else:
            l=QLabel()
        if not field:
            is_field = False
            if txt:
                if isinstance(txt,str):
                    text = txt
                    value = txt
                elif isinstance(txt,dict):
                    text = txt.get('show')
                    value = txt.get('value')
            else:
                valid = False
                while not valid:
                    text,result = QInputDialog.getText(self,_('Insert text for header cell'),_('Text'),text=text)
                    if not result:
                        return None
                    if not text:
                        self.showInfo(_('No text inserted'))
                        return None
                    valid = not self.isTextField(text)
                    value = text
        else:
            is_field = True
            text = "[{}]".format(field)
            value = "_@{}@_".format(text)

        if is_field:
            l.setTextFormat(Qt.RichText)
            l.setText('<b>{}</b>'.format(text))
        else:
            l.setText(text)
        l.setAlignment(align)
        self.tcontent.setdefault(key,{'pix':None, 'txt':None, 'align': 'center'})
        txtdict = {'value': value, 'show': valuefield if valuefield else value }
        self.tcontent[key]['txt'] = txtdict
        self.ui.headerTable.setCellWidget(y,x,l)
        for b in [self.ui.alignCenterButton,self.ui.alignLeftButton,self.ui.alignRightButton]:
            b.setEnabled(True)
        if align == Qt.AlignCenter:
            self.ui.alignCenterButton.setDisabled(True)
        elif align == Qt.AlignLeft|Qt.AlignVCenter:
            self.ui.alignLeftButton.setDisabled(True)
        elif align == Qt.AlignRight|Qt.AlignVCenter:
            self.ui.alignRightButton.setDisabled(True)
        self.ui.emptyButton.setEnabled(True)
        self.ui.splitButton.setDisabled(True)
        for b in [self.ui.imageButton,self.ui.studentNameButton,self.ui.groupButton,self.ui.dateButton]:
            b.setDisabled(True)
        self.ui.textButton.setDisabled(is_field)

    @Slot()
    def studentClicked(self):
        self.textClicked(field='{}'.format(_('Student name field')),valuefield='{}'.format(_('Name')))

    @Slot()
    def dateClicked(self):
        self.textClicked(field='{}'.format(_('Date field')),valuefield='{}'.format(_('Date')))

    @Slot()
    def groupClicked(self):
        self.textClicked(field='{}'.format(_('Group field')),valuefield='{}'.format(_('Group')))

    @Slot()
    def splitClicked(self):
        t = self.getSingleSelection()
        if t:
            y,x = t
        else:
            return
        y_span = self.ui.headerTable.rowSpan(y,x)
        x_span = self.ui.headerTable.columnSpan(y,x)
        if y_span != 1:
            # self.showInfo('Span vertically')
            self.ui.headerTable.setSpan(y,x,1,1)
            key = self.makeKey(y,x)
            del self.tjoins[key]
            self.adjustImages()
            self.ui.splitButton.setDisabled(True)
            self.ui.joinButton.setDisabled(False)
        elif x_span != 1:
            # self.showInfo('Span horizontally')
            self.ui.headerTable.setSpan(y,x,1,1)
            key = self.makeKey(y,x)
            del self.tjoins[key]
            self.adjustImages()
            self.ui.splitButton.setDisabled(True)
            self.ui.joinButton.setDisabled(False)
        else:
            self.showInfo('No span detected')

    @Slot()
    def joinClicked(self, selection=None):
        if selection:
            sel = selection
        else:
            sel = self.getSelection()
            qDebug("{}".format(sel))
        if not sel:
            self.showInfo(_('No cell selected'))
            return
        if not sel.get('good'):
            self.showInfo(_('Not a valid selection'))
            return
        if sel.get('single'):
            self.showInfo(_('Single element can not be joined'))
            return
        items = sel.get('items')
        if not items:
            return
        join_rows = sel.get('join_rows')
        join_cols = sel.get('join_cols')
        span_y = 1
        span_x = 1
        if join_rows:
            span_x = len(items)
        else:
            span_y = len(items)
        self.ui.headerTable.setSpan(items[0][0],items[0][1],span_y,span_x)
        key = self.makeKey(items[0][0],items[0][1])
        self.tjoins[key]=(span_y,span_x)
        self.adjustImages()
        self.ui.joinButton.setDisabled(True)
        self.ui.splitButton.setDisabled(False)

    def removeWidgetsTable(self):
        if getattr(self,'nrows',None) and getattr(self,'ncols',None):
            for y in range(self.nrows):
                for x in range(self.ncols):
                    self.ui.headerTable.removeCellWidget(y,x)

    def getWidgetsTable(self):
        l = []
        for y in range(self.nrows):
            for x in range(self.ncols):
                w = self.ui.headerTable.cellWidget(y,x)
                if w:
                    l.append((y,x,w))
        return l

    def resizeImage(self, *args):
        row = None
        col = None
        widget = None
        if len(args) == 1 and isinstance(args[0],tuple):
            args = args[0]
        if len(args) in [2,3]:
            row = args[0]
            col = args[1]
            widget = self.ui.headerTable.cellWidget(row,col)
        elif len(args) == 1:
            widget = args[0]
            if isinstance(widget,QLabel):
                fn = lambda x: (x[0],x[1]) if x[2] == widget else None
                pos = filter(fn,self.getWidgetsTable())
                if pos:
                    row = pos[0]
                    col = pos[1]
        else:
            return

        tsize = self.ui.headerTable.rect()
        w = int(tsize.width()/self.ncols)
        h = int(tsize.height()/self.nrows)

        if row is not None and col is not None:
            key = self.makeKey(row,col)
            pix = self.tcontent.get(key).get('pix')
        elif widget:
            pix = widget.pixmap()
        if pix:
            pix = loadPixMapData(pix)
            widget.setPixmap(pix.scaled(w,h,Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def updateN(self):
        self.ui.headerTable.setColumnCount(self.ncols)
        self.ui.headerTable.setRowCount(self.nrows)
        self.adjustImages()

    def makeConnections(self):
        self.ui.headerTable.itemSelectionChanged.connect(self.selectionMultiple)
        self.ui.columnSlider.valueChanged.connect(self.setNCols)
        self.ui.rowSlider.valueChanged.connect(self.setNRows)
        self.ui.cancelButton.clicked.connect(self.closeEvent)
        self.ui.acceptButton.clicked.connect(self.storeChanges)
        self.ui.imageButton.clicked.connect(self.imageClicked)
        self.ui.textButton.clicked.connect(self.textClicked)
        self.ui.joinButton.clicked.connect(self.joinClicked)
        self.ui.splitButton.clicked.connect(self.splitClicked)
        self.ui.dateButton.clicked.connect(self.dateClicked)
        self.ui.studentNameButton.clicked.connect(self.studentClicked)
        self.ui.groupButton.clicked.connect(self.groupClicked)
        self.ui.alignCenterButton.clicked.connect(self.alignItem)
        self.ui.alignRightButton.clicked.connect(self.alignItem)
        self.ui.alignLeftButton.clicked.connect(self.alignItem)
        self.ui.emptyButton.clicked.connect(self.emptyCell)

    def storeChanges(self):
        self.backupData = self.dumpData()
        self.hide()

    def centerGeometry(self):
        if not self._parent:
            return
        wg = self._parent.geometry()
        dg = self.geometry()
        dx = (wg.width()-dg.width())/2
        dy = (wg.height()-dg.height())/2
        self.setGeometry(wg.x()+dx,wg.y()+dy,dg.width(),dg.height())
    
    def show(self):
        self.centerGeometry()
        super().show()

    def showInfo(self, text='',timeout=2):
        if timeout and text:
            QTimer.singleShot(timeout*1000,self.showInfo)
        self.ui.infoLabel.setText("{}".format(text))
        if text:
            self.ui.iconInfoLabel.setPixmap(QIcon.fromTheme('dialog-error').pixmap(self.ui.infoLabel.height(),self.ui.infoLabel.height()))
        else:
            self.ui.iconInfoLabel.setPixmap(QPixmap())

    def getUsedCells(self):
        l = list(map(lambda x: (x[0],x[1]),self.getWidgetsTable()))
        return l

    @Slot(int)
    def setNRows(self, n):
        cells = self.getUsedCells()
        if cells:
            y,x = max(cells,key=lambda a: a[0])
            if n-1 < y:
                self.ui.rowSlider.setValue(y+1)
                self.showInfo(_('Remove content first'))
                return None
        self.nrows = n
        self.ui.valueNRowSlider.setText(str(n))
        self.updateN()

    @Slot(int)
    def setNCols(self, n):
        cells = self.getUsedCells()
        if cells:
            y,x = max(cells,key=lambda a: a[1])
            if n-1 < x:
                self.ui.columnSlider.setValue(x+1)
                self.showInfo(_('Remove content first'))
                return None
        self.ncols = n
        self.ui.valueNColumnSlider.setText(str(n))
        self.updateN()

    def makeKey(self,*args):
        return '_'.join([ str(x) for x in args ])

    @Slot()
    def selectionMultiple(self):
        sel = self.getWidgetsIntoSelection()
        if sel:
            single = len(sel) == 1
            hasWidgets = len([t[0] for t in sel if t[0]]) > 0
            for b in [self.ui.textButton,self.ui.imageButton,self.ui.studentNameButton,self.ui.dateButton,self.ui.groupButton]:
                b.setDisabled(hasWidgets)
            if single:
                self.ui.joinButton.setDisabled(True)
                self.ui.splitButton.setDisabled(True)
                w,y,x = sel[0]
                key = self.makeKey(y,x)
                if key in self.tcontent:
                    self.ui.emptyButton.setEnabled(True)
                    align = self.tcontent[key].get('align')
                    if align:
                        for b in [self.ui.alignCenterButton,self.ui.alignLeftButton,self.ui.alignRightButton]:
                            if align in b.objectName().lower():
                                b.setDisabled(True)
                            else:
                                b.setEnabled(True)
                    txt = self.tcontent[key].get('txt')
                    if txt and not self.isTextField(txt.get('show')):
                        self.ui.textButton.setEnabled(True)
                else:
                    self.ui.emptyButton.setEnabled(False)
                if self.haveSpan(y,x):
                    self.ui.splitButton.setEnabled(not hasWidgets)
                else:
                    self.ui.splitButton.setEnabled(False)
            elif single == False:
                self.ui.joinButton.setDisabled(hasWidgets)
                self.ui.splitButton.setDisabled(True)
                for b in [self.ui.alignCenterButton,self.ui.alignLeftButton,self.ui.alignRightButton]:
                    b.setDisabled(True)
                self.ui.emptyButton.setDisabled(True)
            return not single
        return None

    def haveSpan(self, row, col):
        if self.ui.headerTable.rowSpan(row, col) > 1:
            return True
        elif self.ui.headerTable.columnSpan(row, col) > 1:
            return True
        return False

    def eventFilter(self,source,event):
        if source == self.ui.headerTable.viewport():
            if event.type() == QEvent.Type.MouseButtonRelease:
                self.selectionMultiple()
                # qDebug('{}'.format(event.type()))
        return False
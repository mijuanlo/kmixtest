from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Config import DEBUG_LEVEL, ICONS
from .TableDrawer import tableDrawer
from .UpdatePool import UpdatePool
from .Util import Direction, Color, mychr, unmychr
from .Helper import Helper
from .QuestionType import Question

# Class for helping related qt functions for table questions
class tableHelper(QObject):
    # Signals triggered from delegated class
    # Cellmoveclick trigger movement for any row
    cellMoveClick = Signal(int,str)
    # editingquestion trigger editor for cell string 
    editingQuestion = Signal(int)
    # title changed
    questionChanged = Signal(int)
    # rowSelection trigger selection for a question
    rowSelection = Signal(int)
    #
    tableChanged = Signal()

    # class initialization with:
    #  table: qtablewidget view
    def __init__(self, table=None, parent=None):
        global DEBUG_LEVEL
        self.debug_level = DEBUG_LEVEL

        QObject.__init__(self)
        if parent:
            # link to parent as controller for calling functions, events or sending data back
            self.controller = parent

        if table:
            self.number_columns_to_set_into_model = 6
            self.private_last_columns = 2
            self.headerItemNames = []
            # initialize internal data with table data
            self.setTableView(table)
            # connect signals from table with local functions as callback
            self.cellMoveClick.connect(self.moveRow)
            # set delegate class for customizing view from model data
            self.delegate = tableDrawer(self)
            table.setItemDelegate(self.delegate)
        # local string representing table rows selection
        # this state represents number of rows, and state linked or fixed for each row
        self.stateString = ''
        # create new cachedresolver for query movements
        #self.resolver = ResolverCached()
        self.pool = UpdatePool(self)

    # initialize internal data from table provided and setup table for store and view questions
    # initialize callbacks for custom menu on cells
    # initialize callcacks for click on cells
    def setTableView(self, table):
        self.table = table
        # Maybe create own model in future
        # (model) QStandardItemModel(0,5)
        # (view) setModel(self.model)
        self.table.setColumnCount(self.number_columns_to_set_into_model)
        self.model = table.model()
        # Last column is hidden, private data here
        for x in range(1,self.private_last_columns+1):
            self.table.setColumnHidden(self.table.columnCount()-x,True)
        self.configureHeader()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.customMenu)
        self.table.cellClicked.connect(self.ClickOnCell)
        self.table.cellChanged.connect(self.cellChanged)

    def rowEditionPermitted(self,row):
        return self.controller.rowEditionPermitted(self.getCellContent(row,'_UUID_'))

    @Slot(int,int)
    def cellChanged(self, row, col):
        qDebug('Cell changed y={} x={}'.format(row,col))
        self.questionChanged.emit(row)

    def dumpTableModel(self):
        dumpColumns = ['fixed','linked','title','_TYPE_']
        columns = [ self.headerItemNames.index(x) for x in dumpColumns ]
        NUM_ROWS = self.model.rowCount()
        model = list()
        for y in range(NUM_ROWS):
            row = list()
            for x in columns: 
                row.append(self.getCellContent(y,x))
            model.append(row)
        return model

    def updateTitleRow(self,row_uuid,content):
        for y in range(self.model.rowCount()):
            uid = self.model.data(self.model.index(y,self.headerItemNames.index('_UUID_')),Qt.UserRole)
            if uid == row_uuid:
                self.model.setData(self.model.index(y,self.headerItemNames.index('title')),content,Qt.DisplayRole)
                break
    # Create header for tableview
    def configureHeader(self):
        self.headerItemNames = []
        header  = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(i)
            if item:
                header.setSectionResizeMode(i,QHeaderView.ResizeToContents)
                self.headerItemNames.append(str.lower(item.text()))
            else:
                #self.headerItemNames.append("PRIVATE")
                if i == 4:
                    self.headerItemNames.append("_UUID_")
                if i == 5:
                    self.headerItemNames.append("_TYPE_")
        self.table.horizontalHeader().setStretchLastSection(True)

    # Update internal statestring used by resolver
    # Need to update statestring when rows are modified
    def updateStateString(self):
        self.stateString = self.getStateString()
        #self.resolver.reset()
        self.pool.set_stateString(self.stateString)
        self.tableChanged.emit()

    # build new state string representing table
    # two digit with value of 0 (disabled) or 1 (enabled) from each row, representing fixed and linked cells
    def getStateString(self):
        FIXED_COL = self.headerItemNames.index('fixed')
        LINKED_COL = self.headerItemNames.index('linked')
        NUM_COLS = self.model.columnCount()
        NUM_ROWS = self.model.rowCount()
        states = ''
        for y in range(NUM_ROWS):
            for x in [ FIXED_COL, LINKED_COL ]:
                states += '1' if self.model.data(self.model.index(y,x),Qt.DisplayRole) else '0'
        #if self.controller:
        #    self.controller.window.statusbar.showMessage("State = {}".format(states),10*1000)
        return states
    
    # call update graphics from native widget to update movement buttons
    def updateCellGraphics(self,rows='all',cols='all'):
        if rows == 'all':
            rows = list(range(self.model.rowCount()))
        if cols == 'all':
            cols = list(range(self.model.columnCount()))
        if self.debug_level > 1:
            qDebug('Updating graphics for {} {}'.format(rows,cols))
        if not isinstance(rows,list) and not isinstance(cols,list):
            return
        for y in rows:
            for x in cols:
                self.table.update(self.model.index(y,x))
    
    def setCellContent(self,row=None,col=None,values=None,named=False):
        return self.manipulateCellContent(mode='SET',row=row,col=col,values=values,named=named)

    def getCellContent(self,row=None,col=None,named=False):
        return self.manipulateCellContent(mode='GET',row=row,col=col,values=None,named=named)

    def manipulateCellContent(self,mode='GET',row=None,col=None,values=None,named=False):
        if mode == 'SET' and values is None:
            raise ValueError()
        if col is None:
            col = list(range(self.table.columnCount()))
        if row is None:
            row = list(range(self.table.rowCount()))

        retry = False
        if not isinstance(col,list):
            col = [ col ]
            retry = True
        if not isinstance(row,list):
            row = [ row ]
            retry = True
        if retry:
            return self.manipulateCellContent(mode=mode,row=row,col=col,values=values,named=named)
        
        for i in range(len(col)):
            if isinstance(col[i],str):
                if col[i] in self.headerItemNames:
                    col[i] = self.headerItemNames.index(col[i])
                else:
                    raise ValueError()
            elif not isinstance(col[i],int):
                raise ValueError()
            if col[i] < 0 or col[i] >= self.number_columns_to_set_into_model:
                raise ValueError()
        for i in range(len(row)):
            if not isinstance(row[i],int):
                raise ValueError()
            if row[i] < 0 or row[i] >= self.table.rowCount():
                raise ValueError()
        
        result = []
        if len(row) == 1 and len(col) == 1:
            putvalue = '_None'
            if mode == 'SET':
                if isinstance(values,(list)):
                    if len(values) != 1:
                        raise ValueError()
                    if isinstance(values[0],(list)):
                        if len(values[0]) != 1:
                            raise ValueError()
                        else:
                            putvalue = values[0][0]
                    else:
                        putvalue = values[0]
                elif isinstance(values,dict):
                    raise ValueError("TODO!")
                else:
                    putvalue = values
                if putvalue == '_None':
                    raise ValueError()
            role = Qt.DisplayRole
            name = self.headerItemNames[col[0]]
            if name[0] == "_":
                role = Qt.UserRole
            if mode == 'GET':
                value = self.model.data(self.model.index(row[0],col[0]),role)
            elif mode == 'SET':
                self.model.setData(self.model.index(row[0],col[0]),putvalue,role)
                return
            else:
                raise ValueError()
            if named:
                return {name:value}
            else:
                return value
        elif len(row) == 1 and len(col) != 1:
            result = []
            result_dict = {}
            putvalue = '_None'
            if mode == 'SET':
                if isinstance(values,(list)):
                    if len(values) != 1 or len(values) != len(col):
                        raise ValueError()
                    if isinstance(values[0],(list)):
                        if len(values[0]) != len(col):
                            if len(values[0])==1:
                                putvalue = values[0] * len(col)
                            else:
                                raise ValueError()
                        else: # matrix 1xN
                            putvalue = values[0]
                    else: # list(N)
                        if len(values) == 1:
                            putvalue = values * len(col)
                        else:
                            raise ValueError()     
                elif isinstance(values,dict):
                    raise ValueError("TODO!")
                else:
                    putvalue = [ values ] * len(col)
                if len(putvalue) != len(col):
                    raise ValueError()
                if putvalue == '_None':
                    raise ValueError()
            i=0
            for x in col:
                role = Qt.DisplayRole
                name = self.headerItemNames[x]
                if name[0] == "_":
                    role = Qt.UserRole
                if mode == 'GET':
                    value = self.model.data(self.model.index(row[0],x),role)
                    if named:
                        result_dict.setdefault(name,value)
                    else:
                        result.append(value)
                elif mode == 'SET':
                    self.model.setData(self.model.index(row[0],x),putvalue[i],role)
                    i+=1
                else:
                    raise ValueError()
            if mode == 'SET':
                return
            if named:
                return [result_dict]
            else:
                return result
        elif len(row) != 1 and len(col) == 1:
            result = []
            putvalue = '_None'
            if mode == 'SET':
                if isinstance(values,(list)):
                    if len(values) != 1 or len(values) != len(row):
                        raise ValueError()
                    if isinstance(values[0],(list)):
                        if len(values[0]) != len(row):
                            if len(values[0])==1:
                                putvalue = []
                                for i in range(0,len(row)):
                                    putvalue.insert(i,values[0])
                            else:
                                raise ValueError()
                        else: # matrix 1xN
                            putvalue = values[0]
                    else: # list(N)
                        putvalue = []
                        for i in range(0,len(row)):
                            putvalue.insert(0,values[0])
                elif isinstance(values,dict):
                    raise ValueError("TODO!")
                else:
                    putvalue = []
                    for x in range(len(row)):
                        putvalue.append([values])
                if len(putvalue) != len(row):
                    raise ValueError()
                if putvalue == '_None':
                    raise ValueError()
            i=0
            for y in row:
                role = Qt.DisplayRole
                name = self.headerItemNames[col[0]]
                if name[0] == "_":
                    role = Qt.UserRole
                if mode == 'GET':
                    value = self.model.data(self.model.index(y,col[0]),role)
                    if named:
                        result.append({name:value})
                    else:
                        result.append(value)
                elif mode == 'SET':
                    self.model.setData(self.model.index(y,col[0]),putvalue[i][0],role)
                    i+=1
                else:
                    raise ValueError()
            return result
        elif len(row) != 1 and len(col) != 1:
            result = []
            putvalues = []
            if mode == 'SET':
                if isinstance(values,(list)):
                    if len(values) != len(row):
                        if len(values) == 1:
                            if not isinstance(values[0],list):
                                values[0]=[values[0]]
                            for i in range(1,len(row)):
                                values.append(values[0])
                        else:
                            raise ValueError()
                    for v in range(len(values)):
                        if not isinstance(values[v],(list)):
                            raise ValueError()
                        if len(values[v]) != len(col):
                            if len(values[v]) == 1:
                                values[v]=values[v] * len(col)
                            else:
                                raise ValueError()
                        putvalues.append(values[v])
                elif isinstance(values,dict):
                    raise ValueError("TODO!")
                else:
                    putvalues = []
                    for y in range(len(row)):
                        putvalues.append([values]*len(col))
                if not putvalues:
                    raise ValueError()
                if len(putvalues) != len(row):
                    raise ValueError()
                for i in range(len(putvalues)):
                    if len(putvalues[i]) != len(col):
                        raise ValueError()
            i=0
            for y in row:
                j=0
                sub_result = []
                sub_result_dict = {}
                for x in col:
                    role = Qt.DisplayRole
                    name = self.headerItemNames[x]
                    if name[0] == "_":
                        role = Qt.UserRole
                    if mode == 'GET':
                        value = self.model.data(self.model.index(y,x),role)
                        if named:
                            sub_result_dict.setdefault(name,value)
                        else:
                            sub_result.append(value)
                    else:
                        self.model.setData(self.model.index(y,x),putvalues[i][j],role)
                        j+=1
                i+=1
                if mode == 'GET':
                    if named:
                        result.append(sub_result_dict)
                    else:
                        result.append(sub_result)
            return result
        else:
            raise ValueError()

    # Callback from delegate class when click is done on cells linked (col 2) or fixed (col 1)
    @Slot(int, int)
    def ClickOnCell(self, row, column):
        #
        # Method manager for click linkable, lockable cells, no movement here
        #
        FIXED_COL = self.headerItemNames.index('fixed')
        LINKED_COL = self.headerItemNames.index('linked')

        if column not in [ FIXED_COL , LINKED_COL ]:
            return True
        
        FIRST_COL = 0 
        FIRST_ROW = 0
        NUM_COLS = self.model.columnCount()
        NUM_ROWS = self.model.rowCount()
        LAST_COL = NUM_COLS -1
        LAST_ROW = NUM_ROWS -1

        # if there isn't a minium of two rows, linked action isn't available
        if NUM_ROWS < 2 and column == LINKED_COL:
            return True

        # get cell state for a row and col
        def getCellState(row,col):
            return self.model.data(self.model.index(row,col),Qt.DisplayRole)
        # set cell state for a row and col
        def putCellState(row,col,state):
            self.model.setData(self.model.index(row,col),state,Qt.DisplayRole)
        # flip state for a row and col, support one or more rows and cols passing lists
        def flipCellState(rows,cols):
            if not isinstance(rows,list):
                rows = [ rows ]
            if not isinstance(cols,list):
                cols = [ cols ]
            invalidate = False
            for r in rows:
                for c in cols:
                    putCellState(r,c,not getCellState(r,c))
                    invalidate = True
            return invalidate
        # one alone row, can't be linked, minium linked rows are two
        # remove alone linked states
        def removeAloneLinks():
            remove_linked_rows = []
            if NUM_ROWS > 1:
                for r in range(FIRST_ROW,NUM_ROWS):
                    current_is_linked = getCellState(r,LINKED_COL)
                    next_is_linked = getCellState(r+1,LINKED_COL)
                    prev_is_linked = getCellState(r-1,LINKED_COL)
                    if r == FIRST_ROW and current_is_linked and not next_is_linked:
                        remove_linked_rows.append(r)
                        continue
                    if r == LAST_ROW and current_is_linked and not prev_is_linked:
                        remove_linked_rows.append(r)
                        continue
                    if current_is_linked and not next_is_linked and not prev_is_linked:
                        remove_linked_rows.append(r)
                        continue
            for r in remove_linked_rows:
                putCellState(r,LINKED_COL,False)

        columns = [ column ]
        rows = [ row ]
        # if click was on linked cell, link with next or previous cell
        # linked rows will be stored into list
        if column == LINKED_COL:
            CURRENT_STATE = getCellState(row,LINKED_COL)
            if CURRENT_STATE == False:
                # Links two rows on first linking
                if row == FIRST_ROW:
                    if row < LAST_ROW and not getCellState(row+1,LINKED_COL):
                        rows.append(row+1)
                else:
                    if row < LAST_ROW and not getCellState(row+1,LINKED_COL) and not getCellState(row-1,LINKED_COL):
                        rows.append(row+1)

        # Flip state for list of rows and cols
        if flipCellState(rows,columns):
            removeAloneLinks()
            self.updateStateString()
            self.updateCellGraphics(rows='all',cols=[self.headerItemNames.index('order')])
        return True

    # Build custom menu for each row
    @Slot(QPoint)
    def customMenu(self, position):
        item = self.table.itemAt(position)
        if not item:
            qDebug("No item on that position!")
            return
        qDebug("item on x:{} y:{} with value {}".format(item.column(),item.row(),item.text()))
        qm = QMenu('titulo', self.table)
        if item.column()!=0:
            for seq in range(1,4):
                qm.addAction(Helper.genAction(name="ContextAction{}_{}".format(seq,item.text()),fn=self.printContextAction,data="ContextAction_{}_Data".format(seq,item.text()),icon=ICONS['option'],shortcut=None,tip="TipContextAction_{}".format(seq,item.text()),parent=qm))
            qm.addAction(Helper.genAction(name="Delete line '{}'".format(item.text()),fn=self.deleteContextAction,data=item.row(),icon=ICONS['option'],shortcut=None,tip="TipContextAction_Delete_{}".format(item.text()),parent=qm))
        else:
            self.makeLinkedAction(item.row())
        qm.exec_(QCursor.pos())

    # Callback for print on statusbar action triggered from contextmenu
    @Slot()
    def printContextAction(self):
        data = self.sender().data()
        qDebug("senderData:{}".format(data))
        if self.controller:
            self.controller.window.statusbar.showMessage("Action from '{}' triggered".format(data),10*1000)

    # Callback for delete row action triggered from contextmenu
    @Slot()
    def deleteContextAction(self):
        data = self.sender().data()
        self.deleteItem(data)
        if self.controller:
            self.controller.window.statusbar.showMessage("Deleted row {}".format(data),10*1000)

    def deleteItem(self, item):
        if item and isinstance(item,list):
            for i in item:
                self.deleteItem(i)
        else:
            self.table.removeRow(item)
            self.updateStateString()

    def clearTable(self):
        for x in range(self.table.rowCount(),-1,-1):
            self.table.removeRow(x)
        self.updateStateString()

    def newResultCompleted(self,row,dir,result):
        if self.debug_level > 1:
            qDebug('(tablehelper) New result: \'{}\' \'{}\' \'{}\''.format(row,dir,result))
        
        LINKED_COLUMN = self.headerItemNames.index('linked')
        NUM_ROWS = self.model.rowCount()

        if NUM_ROWS < 3:
            self.updateCellGraphics()
            return 

        def getCellState(row,col):
            return self.model.data(self.model.index(row,col),Qt.DisplayRole)
        
        rows = []
        if getCellState(row,LINKED_COLUMN):
            rows.append(row)
            for i in range(row,-1,-1):
                if getCellState(i,LINKED_COLUMN):
                    rows.append(i)
                else:
                    break
            for i in range(row,NUM_ROWS):
                if getCellState(i,LINKED_COLUMN):
                    rows.append(i)
                else:
                    break
            self.updateCellGraphics(rows=rows,cols=[dir])
        else:
            self.updateCellGraphics(rows=[row],cols=[dir])

    # Function called from editorevent manager
    # Check if one row can move up or down taking number, position and states of all rows
    def canMove(self, index, direction):
        if direction not in [Direction.UP.value,Direction.DOWN.value]:
            return False
        # current row searching movement
        ROW = index.row()
        # internal id for selected row
        ID = mychr(ROW)

        ROW_COUNT = index.model().rowCount()
        LINKED_COLUMN = self.headerItemNames.index('linked')
        FIXED_COLUMN = self.headerItemNames.index('fixed')
        
        # First can't go up and Last can't go down
        if ROW == 0 and direction == Direction.UP:
            return False
        if ROW == ROW_COUNT -1 and direction == Direction.DOWN:
            return False
        # Fixed rows can't move
        if index.sibling(ROW,FIXED_COLUMN).data(Qt.DisplayRole):
            return False
        
        # Linked rows with any of them fixed , can't move
        if index.sibling(ROW,LINKED_COLUMN).data(Qt.DisplayRole):
            idx = ROW -1
            # search upward fixed row on linked group
            while idx > 0 and index.sibling(idx,LINKED_COLUMN).data(Qt.DisplayRole):
                if index.sibling(idx,FIXED_COLUMN).data(Qt.DisplayRole):
                    return False
                else:
                    idx -= 1
            # search downward fixed row on linked group
            idx = ROW +1
            while idx < ROW_COUNT and index.sibling(idx,LINKED_COLUMN).data(Qt.DisplayRole):
                if index.sibling(idx,FIXED_COLUMN).data(Qt.DisplayRole):
                    return False
                else:
                    idx += 1

        # Get status from updatepool
        R = self.pool.get_model_dirstate(self.stateString,ROW,direction)

        return True if R else False

    # Callback for move rows triggered from movement buttons on col 0
    # Impossible movements was filtered from delegate class rendering buttons
    # Impossible movements has disabled button that doesn't trigger signal through this callback
    # Parameters:
    # row: (int) number of row that wants to move
    # dir: (string) (UP or DOWN) with movement direction
    @Slot(int,str)
    def moveRow(self,row,dir):
        #
        # Method manager for row movement, impossible movements are filtered from table delegated class event manager
        #

        # Debug function printing model on terminal
        def printModel(m):
            qDebug('MODEL')
            for y in range(0,m.rowCount()):
                s = []
                for x in range(1,m.columnCount()):
                    a=str(m.data(m.index(y,x),Qt.DisplayRole))
                    if a == 'None':
                        a=str(m.data(m.index(y,x),Qt.UserRole))
                    s.append(a)
                qDebug('>{}{}: {}'.format('\t',y,' | '.join(s)))
        
        MODEL = self.table.model()
        # Change to integer for direction
        if dir == 'DOWN':
            dir = Direction.DOWN.value
        else:
            dir = Direction.UP.value

        # Get results from update pool
        R = self.pool.get_model_moveresult(self.stateString,row,dir)
        # Change movements from sequence of chars to list of integers with new rows order
        if R:
            R = [ unmychr(x)-1 for x in R[0] ]
        else:
            self.controller.window.statusbar.showMessage("Thinking... please wait",10*1000)
            return

        # Emit signal while model are changing
        MODEL.layoutAboutToBeChanged.emit()
        # REORDER ROWS TO GET THE SAME ORDER AS ONE RETURNED FROM RESOLVER
        y = -1
        NUM_COLS = MODEL.columnCount()
        NUM_ROWS = MODEL.rowCount()
        done = False
        dest = -1
        while not done:
            changed = False
            dest+=1
            for dest in range(dest,NUM_ROWS):
                if dest != R[dest]:
                    # change rows
                    if self.debug_level > 1:
                        print('CHANGING {} <-> {}'.format(dest,R[dest]))
                        printModel(MODEL)
                    for x in range(1,NUM_COLS):
                        tmp = self.table.takeItem(dest,x)
                        self.table.setItem(dest,x,self.table.takeItem(R[dest],x))
                        self.table.setItem(R[dest],x,tmp)
                    if self.debug_level > 1:
                        printModel(MODEL)

                    # Each model movement must reorder state of result list while ordering for get updated row positions
                    R[R.index(dest)] = R[dest]
                    R[dest] = dest
                    changed = True
            done = not changed

        # Ending with an update of table state
        self.updateStateString()
        # Send signal of end model modification
        MODEL.layoutChanged.emit()
        return

    # Method for create and insert new row triggered for action bar or menu
    def makeRow(self, item="", table=None):
        if table is None and self.table is not None:
            table = self.table
        q = Question().search(item)
        if not q:
            raise ValueError()

        last_row = table.rowCount()
        table.insertRow(last_row)

        # Columns 1,2,3 alignment & size is set from delegated class
        
        # Column 0 is for custom widget up & down movement

        # Columns 1,2 for fixed and linked settings
        #for col in [1,2]:
        self.setCellContent(last_row,['fixed','linked'],False)
            # idx=self.model.index(last_row,col)
            # self.model.setData(idx,False,Qt.DisplayRole)

        # Column 3 for Title

        # i = QTableWidgetItem("{}".format(item))
        # i.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.setCellContent(last_row,'title',"{}:{}".format(last_row,q.getName()))
        #self.model.setData(self.model.index(last_row,3),"{}:{}".format(last_row,title))

        # private columns 4(uuid), 5(type)
    
        # col = self.headerItemNames.index('_UUID_')
        # idx=self.model.index(last_row,col)
        # # Store as UserRole into hidden column
        # self.model.setData(idx,"{}".format(QUuid.createUuid().toString()),Qt.UserRole)
        self.setCellContent(last_row,'_UUID_',"{}".format(QUuid.createUuid().toString()))

        # col = self.headerItemNames.index('_TYPE_')
        # idx=self.model.index(last_row,col)
        # # Store as UserRole into hidden column
        # self.model.setData(idx,"{}".format(q.getNameId()),Qt.UserRole)
        self.setCellContent(last_row,'_TYPE_',"{}".format(q.getNameId()))
        if last_row == 5:
            self.setCellContent(row=[1,2],col=None,values='True')

    def addItem(self, item):
        if item and isinstance(item,list):
            for i in item:
                self.addItem(i)
        else:
            self.makeRow(item)
            self.updateStateString()

    def addItemWithState(self,item,fixed,linked,typequestion):
        self.makeRow(typequestion)
        lastrow = self.model.rowCount()-1
        if fixed:
            FIXED_COL = self.headerItemNames.index('fixed')
            self.model.setData(self.model.index(lastrow,FIXED_COL),fixed,Qt.DisplayRole)
        if linked:
            LINKED_COL = self.headerItemNames.index('linked')
            self.model.setData(self.model.index(lastrow,LINKED_COL),linked,Qt.DisplayRole)
        self.updateStateString()
        self.updateCellGraphics()

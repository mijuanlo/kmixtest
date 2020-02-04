from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Config import DEBUG_LEVEL, ICONS
from .Util import Direction, Color

# Delegate class for questions table logic 
# Allows customize data representation from table model and customize action cells with custom widgets
class tableDrawer(QStyledItemDelegate):
    def __init__(self, helper):
        global DEBUG_LEVEL
        self.debug_level = DEBUG_LEVEL
        super().__init__()
        self.parent = helper
        self.iconFixed = QIcon(ICONS['fixed'])
        self.iconLinked = QIcon(ICONS['linked'])
        self.icons = [ICONS['up'],ICONS['down']]
        self.widgets = []
        for i in self.icons:
            w = QPushButton()
            w.setIcon(QIcon(i))
            #w.setText("UP")
            #w.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.widgets.append(w)

    # POSSIBLE ACTIONS THAT CAN BE REIMPLEMENTED INTO DELEGATE CLASS FOR VIEW THE MODEL DATA OF TABLE
    # (commented, this functions are not needed in this program)

    #def createEditor(self, parent, option, index):
    #    qDebug("CREATE EDITOR")
    #    return super().createEditor(parent, option, index)
    #def setEditorData(self, editor, index):
    #    qDebug("SET EDITOR DATA")
    #    return super().setEditorData(editor, index)
    #def setModelData(self, editor, model, index):
    #    qDebug("SET MODEL DATA")
    #    return super().setModelData(editor, model, index)
    #def sizeHint(self, option, index):
    #    qDebug("SIZE HINT")
    #    return super().sizeHint(option, index)
    #def updateEditorGeometry(self, editor, option, index):
    #    qDebug("UPDATE EDITOR GEOMETRY")
    #    return super().updateEditorGeometry(editor, option, index)
    #def eventFilter(self, editor, event):
    #    handled = super().eventFilter(editor, event)
    #    qDebug("EVENT FILTER {} {} {}".format(editor, event, handled))
    #    return handled

    # Implementation for managing events into table
    def editorEvent(self, event, model, option, index):
        column = index.column()

        # Disable not click release events
        disabled = True
        # Selected row, emit signal for update other view
        if column == 3 and event.type() == QEvent.MouseButtonRelease:
            self.parent.rowSelection.emit(index.row())
        if column == 3 and event.type() == QEvent.MouseButtonDblClick:
            disabled = False
        elif column != 3 and event.type() != QEvent.MouseButtonRelease:
            disabled = False
        if disabled:
            return True
        
        # First column providing up and down movement for rows
        # Model doesn't contain anything for this column
        if column == 0:
            # check what button is pressed thinking on mind that first middle width is for upbutton, rest for downbutton
            offset = option.rect.width() / 2
            if event.x() > offset:
                go = 'DOWN'
                direction = Direction.DOWN.value
            else:
                go = 'UP'
                direction = Direction.UP.value
            # Call for a helper function that manages if cell can be enabled or disabled
            if self.parent.canMove(index,direction):
                # If button was enabled emit signal for movement
                self.parent.cellMoveClick.emit(index.row(),go)
            else:
                # Disable movement not emitting signal
                qDebug("Impossible movement")
            return True # Mark all events on column 0 handled
            # Events on column 0 ends here

        # Events for setting fixed and linked rows
        if column < 3:
            return True # Mark events on cols 1,2 as handled after emitting custom signal
            # Events on columns 1, 2 ends here

        # Column 3 (text) does not handle event here
        if column == 3:
            self.parent.editingQuestion.emit(index.row())

        return super().editorEvent(event, model, option, index) # same as return False

    # Repaint function for question table
    def paint(self, painter, option, index):
        if not index.isValid():
            return
        #if option.state & QStyle.State_Enabled:
        #    qDebug("Painting because state enabled")
        #if option.state & QStyle.State_MouseOver:
        #    qDebug("Painting becaused state mouseover")
        
        CURRENT_COLUMN = index.column()
        ORDER_COLUMN = self.parent.headerItemNames.index('order')
        FIXED_COLUMN = self.parent.headerItemNames.index('fixed')
        LINKED_COLUMN = self.parent.headerItemNames.index('linked')
        QUESTION_COLUMN = self.parent.headerItemNames.index('title')
        
        # First (0) column with movement buttons
        if CURRENT_COLUMN == ORDER_COLUMN:
            count = len(self.widgets)
            # split table cell for two button (up, down)
            size_available = option.rect.width() / count
            DIRECTION_IDX = 0
            for w in self.widgets:
                painter.save()
                ws = w.style()
                opt = QStyleOptionButton()
                opt.rect = option.rect.translated(DIRECTION_IDX*size_available,0)
                opt.rect.setWidth(size_available)
                #opt.text = "{}".format(DIRECTION_IDX)
                opt.icon = w.icon()
                #opt.iconSize = QSize(option.rect.height(),option.rect.height())

                # Set all button state
                if self.parent.canMove(index,DIRECTION_IDX):
                    opt.state = ws.State_Enabled
                else:
                    opt.state = ws.State_Off

                #QApplication.style().drawControl(ws.CE_PushButton,opt,painter,w)
                ws.drawControl(ws.CE_PushButton,opt,painter,w)
                painter.restore()
                DIRECTION_IDX += 1
        # Other cells are: fixed cell , linked cell, question string
        else:
            # set icon for cells 1 and 2
            if CURRENT_COLUMN == FIXED_COLUMN:
                col_icon = self.iconFixed
            if CURRENT_COLUMN == LINKED_COLUMN:
                col_icon = self.iconLinked
            # on model, cells 1 and 2 are represented with boolean data
            cellState = index.data(Qt.DisplayRole)
            if CURRENT_COLUMN != QUESTION_COLUMN:    
                if cellState == True:
                    option.icon = col_icon
                else:
                    option.icon = QIcon()
                option.text = ""
                option.decorationSize = QSize(option.rect.height(), option.rect.height())
                # Must to set position if alignment need to be setted
                option.decorationPosition = QStyleOptionViewItem.Top
                option.decorationAlignment = Qt.AlignCenter
            # cell 3 with question string and no icon
            else:
                option.icon = QIcon()
                option.text = cellState
            
            # draw native text widget or icon widget
            if option.text:
                #super().paint(painter, option, index)
                # same as next call
                option.widget.style().drawControl(QStyle.CE_ItemViewItem,option,painter,option.widget)
            if option.icon or index.data(Qt.DecorationRole):
                option.icon.paint(painter,option.rect,option.decorationAlignment,QIcon.Mode.Normal,QIcon.State.On)

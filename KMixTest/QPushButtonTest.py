from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Config import ICONS

class QPushButtonTest(QPushButton):
    def __init__(self,*args,**kwargs):
        parent = kwargs.get('parent')
        if not parent:
            for i in args:
                if isinstance(i,QWidget):
                    parent = i
        if not parent:
            raise ValueError()
        self._parent = parent
        self.controller = parent.optionController
        
        self.okbwicon = QIcon(ICONS['okbw'])
        self.okicon = QIcon(ICONS['ok'])
        
        buttons = self.controller.buttons()
        if buttons:
            icon = self.okbwicon
        else:
            icon = self.okicon
        if kwargs.get('icon'):
            kwargs['icon'] = icon
        
        for i in range(len(args)):
            found = False
            if isinstance(args[i],QIcon):
                args[i] = icon
                found = True
        if not found:
            largs = list(args)
            largs.insert(0,icon)
            args = tuple(largs)
        
        super().__init__(*args,**kwargs)

        self.controller.addButton(self)
        self.setCheckable(True)
        self.toggled.connect(self.changeIcon)
        self.state = self.isChecked()
        
    @Slot(bool)
    def changeIcon(self,checked):
        if self.state != checked:
            self.state = checked
            if checked == True:
                icon = self.okicon
            else:
                icon = self.okbwicon
            self.setIcon(icon)
            
    def event(self,event):
        if event.type() == QEvent.Type.MouseButtonRelease:
            qDebug("Event in QPushButtonTest {}".format(event.type()))
        return super().event(event)

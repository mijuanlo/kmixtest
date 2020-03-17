from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Config import ICONS

import gettext
_ = gettext.gettext

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

        name = kwargs.get('name')
        if name:
            del kwargs['name']
        else:
            name = id(self)

        self.okbwicon = QIcon(ICONS['okbw'])
        self.okicon = QIcon(ICONS['ok'])
        self.alertbwicon = QIcon(ICONS['alertbw'])
        self.negatedicon = QIcon(ICONS['negated'])

        icon = self.alertbwicon

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

        self.setObjectName(name)
        self.setCheckable(True)
        self.state = None
        self.myStyle()

    def myStyle(self):
        stylesheet = 'background-color: transparent; border: 0px;'
        self.setStyleSheet(stylesheet)

    @Slot(bool)
    def changeIcon(self,checked=None):
        if self.state != checked:
            if checked:
                icon = self.okicon
            elif checked is None:
                icon = self.alertbwicon
            else:
                icon = self.negatedicon
            self.setIcon(icon)
            self.myStyle()
            self.state = checked

    # @Slot()
    # def buttonClicked(self):
    #     self.buttonIsRelesead.emit(self.name)

    def reset(self):
        self.setIcon(self.alertbwicon)
        self.myStyle()
        self.state = None

    # def event(self,event):
    #     if event.type() == QEvent.Type.MouseButtonRelease:
    #         qDebug("Event in QPushButtonTest {}".format(event.type()))
    #     return super().event(event)

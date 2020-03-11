from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Helper import Helper
from .Config import ICONS

class MenuItem(QObject):
    itemActivation = Signal(str)
    def __init__(self,menu=None,name=None,parent=None):
        super().__init__(parent=parent)
        self.children = {}
        self.action = []

        if name and isinstance(name,str):
            self.name = name
        else:
            self.name = 'ROOT'
        
        if menu:
            if isinstance(menu,(QMenuBar,QMenu,QToolBar)):
                self.menu = menu
            else:
                raise ValueError()
        else:
            self.menu = QMenuBar(self)
        
        if parent:
            self.parent = parent
        else:
            self.parent = None

    def getButtons(self):
        return { x.objectName():x for x in self.menu.findChildren(QAbstractButton) if x.objectName() != 'qt_toolbar_ext_button' }

    def emptyMenu(self,on=None):
        if not on:
            on = self.children
        for x in on:
            self.emptyMenu(on=x)
        if self.action:
            for a in self.action:
                a.deleteLater()
        self.children = {}
        self.action = []
        if self.name != 'ROOT':
            self.name = ""
            if self.menu:
                self.menu.deleteLater()

    def _get_names(self):
        if self.name:
            l = [ self.name ]
        else:
            l = []
        for c in self.children:
            l.extend(self.children[c]._get_names())
        return l

    def link_action_button_ids(self):
        try:
            content = self.menu.children()
            for x in content:
                if isinstance(x,QAbstractButton):
                    action = x.defaultAction()
                    if action in content:
                        x.setObjectName(action.objectName())
        except Exception as e:
            pass

    def addMenuItem(self, *args, **kwargs):
        if bool(args) == bool(kwargs):
            raise ValueError()
        if args:
            on = self
            what = args
        elif kwargs:
            on = kwargs.get('on',None)
            what = kwargs.get('what',None)
            if on is None or what is None:
                raise ValueError()
        if not isinstance(on,MenuItem):
            raise ValueError()
        
        if isinstance(what,(list,tuple)):
            for x in what:
                self.addMenuItem(what=x,on=on)
            self.link_action_button_ids()
        elif isinstance(what,dict):
            for k in what:
                if k not in on.children:
                    menuname_with_shortcut = self.calculate_default_menubar_shortcut(k)
                    menu = on.menu.addMenu(menuname_with_shortcut)
                    item = MenuItem(menu=menu,name=k,parent=on)
                    on.children.setdefault(item.name,item)
                else:
                    item = on.children.get(k)
                v = what[k]
                self.addMenuItem(what=v,on=item)
            self.link_action_button_ids()
        elif isinstance(what,str):
            if on.menu:
                if what in ['-','_']:
                    on.menu.addSeparator()
                else:
                    override = False
                    if '|' in what:
                        override = True
                        tmp = what.split('|')
                        what = tmp[0]
                        icon = tmp[1]
                        if icon in ICONS:
                            icon = ICONS[icon]
                        if not what:
                            what = ' '
                    else:
                        icon = ' '
                    characters_data = '()'
                    found = True
                    for x in characters_data:
                        if x not in what:
                            found = False
                            break
                    if found:
                        tmp = what.split('(')
                        what = tmp[0]
                        tmp = tmp[1].split(')')
                        data = tmp[0]
                    else:
                        data = what
                    if on.name == 'ROOT' and not override:
                        icon = None
                    else:
                        icon = QIcon(icon)
                    action = Helper.genAction(name=what,fn=self.emitSignal,icon=icon,tip=what,parent=on.menu,data=data)
                    on.action.append(action)
                    on.menu.addAction(action)
        else:
            raise ValueError()
    
    def emitSignal(self):
        self.itemActivation.emit(self.sender().data())

    def calculate_default_menubar_shortcut(self,name):
        used = []
        # print('names: {}'.format(self._get_names()))
        for item in self._get_names():
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

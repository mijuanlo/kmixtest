from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

# Helper with static functions helping qt gui actions
class Helper():
    def __init__(self):
        pass
    # Generates qtaction with custom parameters
    # Parameters:
    # name: name of qtaction action, must be provided
    # fn: trigger function, must be provided
    # data: static data (string) included into qtaction, optional
    # icon: Qicon or string (filename) for qtaction, optional
    # shortcut: QKeySecuence or string representing shortcut for qtaction, optional
    # tip: string helping describe qtaction when mouse is over, optional
    # parent: parent QtObject, optional
    # Returns: QtAction configured
    @staticmethod
    def genAction(name=None, fn=None, data=None, icon=None, shortcut=None, tip=None, parent=None):
        # name and callback function are mandatory
        if name and fn:
            if icon:
                if isinstance(icon,str):
                    icon = QIcon(icon)
                elif isinstance(icon,QIcon):
                    pass
                else:
                    icon = None
            else:
                icon = None
            # icon can be filename (string) or QIcon
            if icon:
                action = QAction(icon,name,parent)
            else:
                action = QAction(name,parent)
            
            # allow empty data included
            if data != None:
                action.setData(data)
            # allow empty shortcut
            if shortcut:
                if isinstance(shortcut,QKeySequence):
                    pass
                else:
                    try:
                        shortcut = QKeySequence(shortcut)
                    except:
                        shortcut = None
            if shortcut:
                action.setShortcuts(shortcut)
            
            # allow empty tip
            if tip and isinstance(tip,str):
                action.setStatusTip(tip)

            action.triggered.connect(fn)

            return action
        return None       

# import sys
# from PySide2.QtCore import *
# from PySide2.QtWidgets import *
# from PySide2.QtGui import *
# from PySide2.QtPrintSupport import *
# from PySide2.QtUiTools import *
# from sys import exit
# from time import time,sleep
# from enum import Enum,IntEnum,auto,unique
# from os import cpu_count
# from queue import Queue, Empty
# import signal

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
import signal
import sys
from .AppMainWindow import AppMainWindow

def exit_control_c(sig, frame):
    print("User request exit")
    app.exitting()

# Starting point of execution
def start_kmixtest():
    for s in [signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]:
        signal.signal(s, exit_control_c)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = AppMainWindow()
    sys.exit(app.exec_())

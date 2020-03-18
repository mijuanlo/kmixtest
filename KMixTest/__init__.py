from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
import signal
import sys
from .AppMainWindow import AppMainWindow
from .Config import _

app = None
exitting = False

def exit_control_c(sig, frame):
    global app,exitting
    exitting = True
    
    if app:
        print(_("User request exit from app"))
        app.exitting()
    else:
        print(_("Ending QApplication"))
        QApplication.quit()
    
    sys.exit(0)
        

# Starting point of execution
def start_kmixtest(load_filename=None):
    global app, exitting
    for s in [signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]:
        signal.signal(s, exit_control_c)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    try:
        app = AppMainWindow(load_filename)
        if app and not exitting and not app.aborting:
            sys.exit(app.exec_())
    except Exception as e:
        print('{}:{}'.format(_('Initialization exception'),e))
    finally:
        print('{}'.format(_('Quitting Kmixtest')))
        QApplication.quit()
        sys.exit(0)
    

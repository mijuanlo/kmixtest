from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
import signal
import sys
from .AppMainWindow import AppMainWindow

app = None

def exit_control_c(sig, frame):
    global app
    print("User request exit")
    if app:
        app.exitting()

# Starting point of execution
def start_kmixtest():
    global app
    for s in [signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]:
        signal.signal(s, exit_control_c)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = AppMainWindow()
    sys.exit(app.exec_())

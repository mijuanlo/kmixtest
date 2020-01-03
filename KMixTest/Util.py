from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from enum import Enum,IntEnum,auto,unique

@unique
class Direction(IntEnum):
    UP = 0
    DOWN = 1
    FIXED = 2

class Color(Enum):
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m' 
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLINK = '\033[5m'
    UNDERLINE = '\033[4m'

    def makecolor(thing,color):
        if not isinstance(color,Color):
            return
        return '{}{}{}'.format(color.value,thing,Color.RESET.value)

chars = ''
def mychr(num): 
    global chars
    if chars:
        return chars[num]
    else:
        for i in range(49,58):
            chars += chr(i)
        for i in range(65,91):
            chars += chr(i)
        for i in range(97,123):
            chars += chr(i)
        for i in range(192,768):
            chars += chr(i)
def unmychr(char):
    global chars
    if chars:
        return chars.index(char)+1

# Function for debugging page printer configuration
def print_preview_data(preview):
    orientation = preview.orientation().name.decode()
    viewmode = preview.viewMode().name.decode()
    zoommode = preview.zoomMode().name.decode()
    currentPage = preview.currentPage()
    pagecount = preview.pageCount()
    qDebug("(Preview)  {} {} {} {}/{}".format(orientation, viewmode, zoommode, currentPage, pagecount))

def marginsToString(margins):
    return "{} {} {} {}".format(margins.left(),margins.top(),margins.right(),margins.bottom())

# Function for debugging printer configuration
def print_printer_data(printer):
    pr = printer.paperRect()
    layout = printer.pageLayout()
    margins = layout.margins()
    size = layout.pageSize().id().name.decode()
    units = layout.units().name.decode()
    qDebug("(Printer)  Rect: {}x{} Size: {} Margins: {} Unit: {}".format(pr.width(),pr.height(),size,marginsToString(margins),units))

# Function for debugging document configuration
def print_document_data(document):
    size = document.pageSize()
    qDebug('(document) Rect: {}x{}'.format(int(size.width()),int(size.height())))

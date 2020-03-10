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
    if chars and isinstance(char,str):
        return chars.index(char)+1

def picaToPixels(pica):
    return pica * 12

def mmToPixels(mm, printer=None, resolution=1200):
    # 1 pixel per inch (ppi) = 0.03937 pixel per mm (dpi)
    # 1 pixel per mm (dpi)   = 25.4 pixel per inch (ppi)
    # 1 inch = 25.4 mm
    res = None
    if not printer or not isinstance(printer,QPrinter):
        if resolution:
            res = resolution
    else:
        res = printer.resolution()
    if res:
        return mm * 0.039370147 * res
    return None

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

def ftype(numtype):
    if numtype == -1:
        return 'invalid'
    elif numtype == 1:
        return 'block'
    elif numtype == 2:
        return 'char'
    elif numtype == 3:
        return 'list'
    elif numtype == 5:
        return 'frame'
    elif numtype == 100:
        return 'user'
    else:
        return 'unknown'
def otype(numtype):
    if numtype == 0:
        return 'no_object'
    elif numtype == 1:
        return 'image'
    elif numtype == 2:
        return 'table'
    elif numtype == 3:
        return 'tablecell'
    elif numtype == 8:
        return 'userobject'
    else:
        return 'unknown'

def format_info(f):
    attrs = []
    fmt = None
    if not f.isValid():
        attrs.append('Invalid')
    else:
        attrs.append('Valid')
        if f.isBlockFormat():
            attrs.append('BlockFormat')
            fmt = f.toBlockFormat()
        elif f.isCharFormat():
            attrs.append('CharFormat')
            fmt = f.toCharFormat()
        elif f.isFrameFormat():
            attrs.append('FrameFormat')
            fmt = f.toFrameFormat()
        elif f.isImageFormat():
            attrs.append('ImageFormat')
            fmt = f.toImageFormat()
        elif f.isTableFormat():
            attrs.append('TableFormat')
            fmt = f.toTableFormat()
        elif f.isTableCellFormat():
            attrs.append('TableCellFormat')
            fmt = f.toTableCellFormat()
        elif f.isListFormat():
            attrs.append('ListFormat')
            fmt = f.toListFormat()
    return ','.join(attrs)
    
# Function for debugging document configuration
def print_document_data(document):
    size = document.pageSize()
    page_w = int(size.width())
    page_h = int(size.height())
    doc_w = int(document.size().width())
    doc_h = int(document.size().height())
    doc_pagecount = document.pageCount()
    qDebug('\n(document) pagesize: {}x{} size: {}x{} pagecount={}'.format(page_w,page_h,doc_w,doc_h,doc_pagecount))
    doc_blockcount = document.blockCount()
    qDebug('(document): {} Blocks'.format(doc_blockcount))
    firstblock = document.firstBlock()
    lastblock = document.lastBlock()
    textblock = firstblock

    acu_height1 = 0
    acu_height2 = 0
    acu_height3 = 0
    while  textblock != lastblock:
        blocknumber = textblock.blockNumber()
        visible = textblock.isVisible()
        linecount = textblock.lineCount()
        text = textblock.text()

        blockformat = textblock.blockFormat()
        charformat = textblock.charFormat()
        type_blockformat = blockformat.type()
        objecttype_blockformat = blockformat.objectType()
        type_charformat = charformat.type()
        objecttype_charformat = charformat.objectType()
        lineheight = int(blockformat.lineHeight())
        
        qDebug('\n(document) block #{} type={} otype={} charformat type={} otype={}'.format(blocknumber,ftype(type_blockformat),otype(objecttype_blockformat),ftype(type_charformat),otype(objecttype_charformat)))
        qDebug('(document) block is: {}'.format(format_info(blockformat)))        
        qDebug('#{} visible={} text="{}" linecount={} lineheight={}'.format(blocknumber,visible,text,linecount,lineheight))

        rect = textblock.layout().boundingRect()
        rect2 = document.documentLayout().blockBoundingRect(textblock)
        w = int(rect.width())
        h = int(rect.height())
        h2y = int(rect2.y())
        h2 = int(rect2.height())

        qDebug('Bounding {} (sum_heights) vs {} (y)'.format(acu_height1,h2y))

        acu_height1 += h
        acu_height2 += h2

        #pagenumber = int(acu_height2/page_h)+1
        pagenumber = int(h2y/page_h)+1
        qDebug('#{} block into page={}'.format(blocknumber,pagenumber))
        qDebug('#{} bounding rect:  x=[(block){} (page){} (doc){}] y=[(block){} (page){} (doc){}] acu1={} acu2={}'.format(blocknumber,w,page_w,doc_w,h,page_h,doc_h,acu_height1,acu_height2))

        it = textblock.begin()
        i = 0
        while(it != textblock.end()):
            if i == 0:
                qDebug('#{} StartFragments'.format(blocknumber))
            frag = it.fragment()
            if not frag.isValid():
                qDebug('Not VALID')
            else:
                frag_charformat = frag.charFormat()
                qDebug('#{} (Fragment #{}) Text: "{}"'.format(blocknumber,i,frag.text()))
                qDebug('#{} (Fragment #{}) Type charformat: {}'.format(blocknumber,i,ftype(frag_charformat.type())))
                qDebug('#{} (Fragment #{}) Type object charformat: {}'.format(blocknumber,i,otype(frag_charformat.objectType())))
            it+=1
            i += 1
        if i == 0:
            qDebug('#{} NoFragments'.format(blocknumber))
        else:
            qDebug('#{} EndFragments'.format(blocknumber))

        textblock = textblock.next()
    qDebug('{}'.format(acu_height2 + document.documentMargin() ))
def dumpPixMapData(pixmap):
    byts = QByteArray()
    buff = QBuffer(byts)
    buff.open(QIODevice.ReadWrite)
    pixmap.save(buff,"PNG")
    buff.close()
    return qCompress(byts).toBase64().data().decode()

def loadPixMapData(data,pixmap=None):
    if not pixmap:
        pixmap = QPixmap()
    byts = QByteArray().fromBase64(data.encode())
    res = pixmap.loadFromData(qUncompress(byts))
    if not res:
        raise ValueError()
    return pixmap

def fileToPixMap(filename):
    pixmap = QPixmap()
    res = pixmap.load(filename)
    if res:
        return pixmap
    return None

def dataPixMapToImage(data):
    pixmap = loadPixMapData(data)
    if pixmap:
        return pixmap.toImage()
    return None
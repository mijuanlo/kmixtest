from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Util import marginsToString, print_document_data, print_preview_data, print_printer_data
from .PreviewPrinter import previewPrinter
from .Config import ARTWORK

# Helper class with pdf stuff related things
class helperPDF():

    header_table_cols = 3
    header_table_rows = 2

    def __init__(self, parent=None):
        self.parent = parent
        self.pageMargins = QMarginsF(10,10,10,10)
        self.orientation = QPageLayout.Orientation.Portrait
        self.layout = None
        self.printer = None
        self.resolution = QPrinter.HighResolution
        self.constPaperScreen = None
        self.document = None
        self.cursor = None
        self.styles = None
        self.widget = None
        self.printer, self.resolution, self.constPaperScreen, self.layout = self.initPrinter(printer=self.printer, resolution=self.resolution, margins=self.pageMargins, orientation=self.orientation)
        self.widget = self.initWidget(parent=self, printer=self.printer)
        pass

    def initPrinter(self, printer=None, resolution=QPrinter.HighResolution, margins=None, orientation=None):
        
        if not resolution:
            if self.resolution:
                resolution = self.resolution
            else:
                resolution = QPrinter(QPrinter.HighResolution).resolution()
                self.resolution = resolution
        
        if isinstance(resolution,QPrinter.PrinterMode):
            default_printer = QPrinter(resolution)
            resolution = QPrinter(resolution).resolution()
        else:
            default_printer = QPrinter()
            default_printer.setResolution(resolution)
            
        if not printer:
            if self.printer:
                printer = self.printer
            else:
                self.printer = default_printer
                printer = default_printer

        if printer.resolution() != resolution:
            printer.setResolution(resolution)
        
        current_layout = self.printer.pageLayout()
        changed_layout = False
        if current_layout.units() != QPageLayout.Millimeter:
            current_layout.setUnits(QPageLayout.Millimeter)
            changed_layout = True

        if margins is not None and isinstance(margins,QMarginsF):
            qDebug("Setting margins to {}".format(marginsToString(margins)))
            current_layout.setMargins(margins)
            changed_layout = True
        else:
            self.pageMargins = current_layout.margins()
        
        if orientation is not None and isinstance(orientation, QPageLayout.Orientation):
            qDebug("Setting orientation to {}".format(orientation.name.decode()))
            current_layout.setOrientation(orientation)
            changed_layout = True

        if changed_layout:
            printer.setPageLayout(current_layout)

        PaperToScreen = int( resolution / QPrinter(QPrinter.ScreenResolution).resolution() )
        self.constPaperScreen = PaperToScreen
        qDebug("Setting constant: {}".format(int(self.constPaperScreen)))

        relTextToA4 = int(self.printer.pageSizeMM().width()/210.0)
        self.relTextToA4 = relTextToA4
        qDebug("Setting text multiplier size: {}".format(relTextToA4))

        return printer, resolution, PaperToScreen, current_layout

    def initDocument(self, printer=None, document=None):
        if not printer:
            printer = self.printer
        if not document:
            document = QTextDocument()
        if not self.document:
            self.document = document
        document.setPageSize(QSize(printer.pageRect().size()))
        self.initStyles()
        return document

    def initWidget(self, parent=None, printer=None):
        
        widget = previewPrinter(parent=parent,printer=printer)
        if not self.widget:
            self.widget = widget
        widget.paintRequested.connect(self.paintRequest)
        return widget 

    def openWidget(self):
        self.widget.exec_()

    def initStyles(self, styles=None):
        
        if not styles:
            styles = {}
            self.styles = styles

        if not 'header.table' in styles:
            styles.setdefault('header.table',QTextTableFormat())
        styles['header.table'].setBorderStyle(QTextTableFormat.BorderStyle_Solid)
        styles['header.table'].setBorder(1.0)
        styles['header.table'].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles['header.table'].setMargin(0.0)
        styles['header.table'].setCellSpacing(0.0)
        styles['header.table'].setCellPadding(10 * self.constPaperScreen)
        styles['header.table'].setColumnWidthConstraints([ QTextLength(QTextLength.PercentageLength, 95/self.header_table_cols) ] * self.header_table_cols)

        styles['centerH'] = QTextBlockFormat()
        styles['centerH'].setAlignment(Qt.AlignCenter)
        
        styles['centerV'] = QTextCharFormat()
        styles['centerV'].setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)

        styles['text'] = QTextCharFormat()
        
        qDebug("Using text multiplier size: {}".format(int(self.relTextToA4)))
        styles['text'].setFont(QFont("Times",10 * self.constPaperScreen * self.relTextToA4))
        return styles


    @Slot(QPrinter)
    def paintRequest(self, printer=None):
        qDebug("***** Repaint Event ! *****")

        self.initPrinter(printer)
        self.document = self.initDocument(printer = self.printer)

        print_document_data(self.document)
        print_printer_data(printer)

        document = self.makeHeaderTable(self.document,self.styles['header.table'] )
        document.print_(printer)
        

    def makeHeaderTable(self, document, style, rows = header_table_rows, cols = header_table_cols, images = ARTWORK):
        def setupCell(row=0,col=0):
            cell = table.cellAt(row,col)
            cursor = cell.firstCursorPosition()
            cursor.setBlockFormat(self.styles['centerH'])
            cell.setFormat(self.styles['centerV'])
            return cursor
        
        max_image_width = (document.pageSize() / cols).width()
        max_image_height = (document.pageSize() / 6).height() # no big headers!
        def imageResized(name):
            image = QImage(name)
            new_image_height = image.height() * max_image_width / image.width()
            image = image.scaled(max_image_width,new_image_height,Qt.KeepAspectRatio,Qt.SmoothTransformation)
            if image.height() > max_image_height:
                new_image_width = image.width() * max_image_height / image.height()
                image = image.scaled(new_image_width,max_image_height,Qt.KeepAspectRatio,Qt.SmoothTransformation)
            return image

        cursor = QTextCursor(document)

        table = cursor.insertTable(rows,cols,self.styles['header.table'])
        first_element_row = 1
        first_element_col = 0
        num_rows = 1
        num_cols = cols

        table.mergeCells(first_element_row,first_element_col,num_rows,num_cols)
    
        cursor = setupCell(0,0)
        cursor.insertImage(imageResized(images['left']))

        cursor = setupCell(0,1)
        cursor.insertImage(imageResized(images['center']))
    
        from random import randint
        a = randint(3,20)
        b = randint(3,20)

        cursor = setupCell(0,2)
        cursor.insertText("Lorem ipsum " * a, self.styles['text'])

        cursor = setupCell(1,0)
        cursor.insertText("Lorem ipsum " * b, self.styles['text'])

        return document


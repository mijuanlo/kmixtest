from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Util import mmToPixels, picaToPixels, marginsToString, print_document_data, print_preview_data, print_printer_data, loadPixMapData, dumpPixMapData, fileToPixMap, dataPixMapToImage
from .PreviewPrinter import previewPrinter
from .Config import ARTWORK, ICONS

from copy import deepcopy

USE_FAKE_HEADER = True

# Helper class with pdf stuff related things
class helperPDF():

    header_table_cols = 3
    header_table_rows = 2

    def __init__(self, parent=None):
        self.debug = False
        self.parent = parent
        self.pageMargins = QMarginsF(10,10,10,10)
        self.orientation = QPageLayout.Orientation.Portrait
        self.layout = None
        self.printer = None
        self.resolution_type = QPrinter.HighResolution
        self.dpi = QPrinter(self.resolution_type).resolution()
        self.constPaperScreen = None
        self.document = None
        self.cursor = None
        self.styles = None
        self.widget = None
        self.printer, self.dpi, self.constPaperScreen, self.layout = self.initPrinter(printer=self.printer, resolution=self.resolution_type, margins=self.pageMargins, orientation=self.orientation)
        self.widget = None
        self.header_info = None
        self.preview = False
        self.last_cursor_ack = None
        self.last_page_ack = 1
        self.numberedPages = True
        self.headerWithFrame = False
        self.splitWithFrame = False
        if self.debug:
            self.headerWithFrame = True
            self.splitWithFrame = True
    def setCustomizations(self,numberedPages, splitWithFrames, headerWithFrame):
        self.splitWithFrame = splitWithFrame
        self.numberedPages = numberedPages
        self.headerWithFrame = headerWithFrame

    def initPrinter(self, printer=None, resolution=QPrinter.HighResolution, margins=None, orientation=None):
        
        if not resolution:
            if self.resolution_type:
                resolution = QPrinter(self.resolution_type).resolution()
                self.dpi = resolution
            else:
                self.resolution_type = QPrinter.HighResolution
                resolution = QPrinter(self.resolution_type).resolution()
                self.dpi = resolution
        
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
            if self.debug:
                qDebug("Setting margins to {}".format(marginsToString(margins)))
            current_layout.setMargins(margins)
            changed_layout = True
        else:
            self.pageMargins = current_layout.margins()
        
        if orientation is not None and isinstance(orientation, QPageLayout.Orientation):
            if self.debug:
                qDebug("Setting orientation to {}".format(orientation.name.decode()))
            current_layout.setOrientation(orientation)
            changed_layout = True

        if changed_layout:
            printer.setPageLayout(current_layout)

        PaperToScreen = int( resolution / QPrinter(QPrinter.ScreenResolution).resolution() )
        self.constPaperScreen = PaperToScreen
        if self.debug:
            qDebug("Setting constant: {}".format(int(self.constPaperScreen)))

        relTextToA4 = int(self.printer.pageSizeMM().width()/210.0)
        self.relTextToA4 = relTextToA4
        if self.debug:
            qDebug("Setting text multiplier size: {}".format(relTextToA4))

        return printer, resolution, PaperToScreen, current_layout

    def initDocument(self, printer=None, document=None):
        if not printer:
            printer = self.printer
        if not document:
            document = ExamDocument()
        if not self.document:
            self.document = document
        document.setHeadersSize(16)
        document.setPage(printer=printer)
        self.initStyles(printer=printer)
        return document

    def initWidget(self, parent=None, printer=None):
        
        widget = previewPrinter(parent=parent,printer=printer)
        if not self.widget:
            self.widget = widget
        widget.paintRequested.connect(self.paintRequest)
        return widget 

    def initSystem(self,printer=None,filename=None):
        self.last_cursor_ack = None
        self.last_page_ack = 1
        if printer:
            self.printer = printer
        self.printer, self.dpi, self.constPaperScreen, self.layout = self.initPrinter(printer=self.printer, resolution=self.resolution_type, margins=self.pageMargins)
        self.document = self.initDocument(printer = self.printer)
        if not self.preview:
            self.printer.setOutputFormat(QPrinter.PdfFormat)
            if filename:
                self.printer.setOutputFileName(filename)
            else:
                self.printer.setOutputFileName('out.pdf')

    def openWidget(self):
        self.preview = True
        self.widget = self.initWidget(parent=self, printer=self.printer)
        self.widget.exec_()

    def writePDF(self):
        self.preview = False
        self.paintRequest()

    def initStyles(self, styles=None, printer=None):
        
        if printer and isinstance(printer,QPrinter):
            resolution = printer.resolution()
        else:
            if self.dpi:
                resolution = self.dpi
            elif self.resolution_type:
                resolution = QPrinter(self.resolution_type).resolution()
            else:
                resolution = QPrinter(QPrinter.HighResolution).resolution()
    
        if not styles:
            styles = {}
            self.styles = styles

        if self.debug:
            tableborder = 1.0
            tableborderstyle = QTextTableFormat.BorderStyle_Solid
        else:
            tableborder = 0.0
            tableborderstyle = QTextTableFormat.BorderStyle_None

        styles['line'] = QTextFrameFormat()
        styles['line'].setHeight(1*self.constPaperScreen*self.relTextToA4)
        styles['line'].setBackground(Qt.black)

        styles['pagebreak'] = QTextBlockFormat()
        styles['pagebreak'].setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)

        x = 'table.common'
        styles[x] = QTextTableFormat()
        styles[x].setBorderStyle(QTextTableFormat.BorderStyle_Solid)
        styles[x].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles[x].setBorder(2.0)
        styles[x].setMargin(0.0)
        styles[x].setCellSpacing(0.0)
        styles[x].setCellPadding(mmToPixels(2,resolution=resolution))

        x = 'header.table'
        styles[x] = QTextTableFormat()
        styles[x].setBorderStyle(QTextTableFormat.BorderStyle_Solid)
        styles[x].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles[x].setBorder(2.0)
        styles[x].setMargin(0.0)
        styles[x].setCellSpacing(0.0)
        styles[x].setCellPadding(mmToPixels(2,resolution=resolution))
        styles['header.table'].setColumnWidthConstraints(
            [ 
                QTextLength(QTextLength.PercentageLength, 95/self.header_table_cols) 
            ] * self.header_table_cols)

        x = 'title.table'
        styles[x] = QTextTableFormat()
        styles[x].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles[x].setMargin(0.0)
        styles[x].setCellSpacing(0.0)
        styles[x].setBorderStyle(tableborderstyle)
        styles[x].setBorder(tableborder)
        styles[x].setCellPadding(0.0)
        styles[x].setColumnWidthConstraints(
            [ 
                QTextLength(QTextLength.PercentageLength, 75), 
                QTextLength(QTextLength.PercentageLength, 25)
            ] )

        x = 'title.table.text'
        styles[x] = QTextTableFormat()
        styles[x].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles[x].setMargin(0.0)
        styles[x].setCellSpacing(0.0)
        styles[x].setBorderStyle(tableborderstyle)
        styles[x].setBorder(tableborder)
        styles[x].setCellPadding(0.0)
        styles[x].setColumnWidthConstraints(
            [ 
                QTextLength(QTextLength.PercentageLength, 99), 
                QTextLength(QTextLength.PercentageLength, 0)
            ] )
        
        x = 'option.table'
        styles[x] = QTextTableFormat()
        styles[x].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles[x].setMargin(0.0)
        styles[x].setCellSpacing(0.0)
        styles[x].setBorderStyle(tableborderstyle)
        styles[x].setBorder(tableborder)
        styles[x].setCellPadding(0.0)
        styles[x].setLeftMargin(mmToPixels(10,resolution=resolution))
        styles[x].setColumnWidthConstraints(
            [ 
                QTextLength(QTextLength.PercentageLength, 5), 
                QTextLength(),
                QTextLength()
            ] )

        x = 'option.table.join'
        styles[x] = QTextTableFormat()
        styles[x].setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
        styles[x].setMargin(0.0)
        styles[x].setCellSpacing(0.0)
        styles[x].setBorderStyle(tableborderstyle)
        styles[x].setBorder(tableborder)
        styles[x].setCellPadding(0.0)
        # styles[x].setColumnWidthConstraints(
        #     [ 
        #         QTextLength(QTextLength.PercentageLength, 95 / 7)
        #     ] * 7 
        #     )
        styles[x].setAlignment(Qt.AlignCenter)

        styles['centerH'] = QTextBlockFormat()
        styles['centerH'].setAlignment(Qt.AlignCenter)
        
        styles['centerV'] = QTextCharFormat()
        styles['centerV'].setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)

        styles['body'] = QTextBlockFormat()
        styles['body'].setAlignment(Qt.AlignJustify)

        styles['double'] = QTextBlockFormat()
        styles['double'].setLineHeight(200,QTextBlockFormat.ProportionalHeight)

        styles['single'] = QTextBlockFormat()
        styles['single'].setLineHeight(100,QTextBlockFormat.ProportionalHeight)
        
        if self.debug:
            qDebug("Using text multiplier size: {}".format(int(self.relTextToA4)))
        
        # styles['defaultfont'] = QFont("Times",10 * self.constPaperScreen * self.relTextToA4)
        # styles['bigfont'] = QFont("Times",30 * self.constPaperScreen * self.relTextToA4)

        styles['defaultfont'] = QFont("Times", picaToPixels(10))
        styles['bigfont'] = QFont("Times", picaToPixels(30))

        styles['text'] = QTextCharFormat()
        styles['bigtext'] = QTextCharFormat()
        styles['text.bold'] = QTextCharFormat()

        styles['text'].setFont(styles['defaultfont'])
        styles['bigtext'].setFont(styles['bigfont'])
        styles['text.bold'].setFont(styles['defaultfont'])
        styles['text.bold'].setFontWeight(QFont.Bold)
        return styles

    def print_cursor_position_y(self,document,cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        page_h = document.pageSize().height()
        layout = document.documentLayout()
        rect = layout.blockBoundingRect(cursor.block())
        current_h = rect.y() + rect.height()
        # page_h -= 2 * mmToPixels(document.headersSize,1200)
        # current_h2 = document.documentLayout().blockBoundingRect(cursor.block()).y()
        pagenumber = int(current_h/page_h)+1
        pagecount = document.pageCount()
        # if self.debug:
        #     qDebug('Cursor at: {} page={}'.format(current_h,pagenumber,pagecount))
        pct = int(current_h*100/page_h)%100
        return pagenumber,pct

    @Slot(QPrinter)
    def paintRequest(self, printer=None):
        if self.debug:
            qDebug("***** Repaint Event ! *****")

        self.initSystem(printer)

        if self.debug:        
            # print_document_data(self.document)
            print_printer_data(self.printer)

        self.document = self.completeDocument(self.document)
        #self.document = self.makeTestDocument(self.document)
        self.document.printExamModel(self.printer,model="A",numbered=self.numberedPages,framed=self.headerWithFrame)

    def makeTestDocument(self,document):
        #Init cursor
        cursor = QTextCursor(document)
        # cursor.movePosition(QTextCursor.End)
        # if cursor.hasSelection():
        #     cursor.clearSelection()
        t={}
        for l in list('abcdefghijk'):
            t[l] = ''
            for i in range(1,20):
                t[l] += '{0:s}_{1:03d}_'.format(l*5,i*10)

        style_t = QTextCharFormat()
        font = QFont("Courier",10 * self.constPaperScreen * self.relTextToA4)
        style_t.setFont(font)
        style_b = QTextBlockFormat()
        style_f = QTextFrameFormat()

        cursor.insertBlock(style_b)
        a = cursor.block()
        a.setUserData(BData('a'))
        cursor.insertText(t.get('a'),style_t)

        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock(style_b)
        b = cursor.block()
        b.setUserData(BData('b'))
        bpos = b.blockNumber()
        cursor.insertText(t.get('b'),style_t)

        cursor.movePosition(QTextCursor.Start)
        cursor.insertBlock(style_b)
        c = cursor.block()
        cursor.insertText(t.get('c'),style_t)

        cursor = QTextCursor(b)
        pos = cursor.position()
        cursor.insertBlock(style_b)
        d = cursor.block()
        cursor.setPosition(pos)
        cursor.insertText(t.get('d'),style_t)

        cursor = QTextCursor(b)
        pos2 = cursor.position()
        cursor.insertBlock(style_b)
        e = cursor.block()
        cursor.setPosition(pos2)
        cursor.insertText(t.get('e'),style_t)

        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock,QTextCursor.MoveAnchor,b.blockNumber())
        pos3 = cursor.position()
        cursor.insertBlock(style_b)
        f = cursor.block()
        cursor.setPosition(pos3)
        cursor.insertText(t.get('f'),style_t)

        cursor.movePosition(QTextCursor.Start)
        while cursor.block().userData() is None or cursor.block().userData().data != 'b':
            cursor.movePosition(QTextCursor.NextBlock,QTextCursor.MoveAnchor,1)
        cursor.setPosition(cursor.position()-1)
        cursor.insertBlock(style_b)
        g = cursor.block()
        cursor.insertText(t.get('g'),style_t)

        cursor.movePosition(QTextCursor.Start)
        tb = cursor.block()
        tb = tb.next().next().next()
        cursor = QTextCursor(tb)
        style_cr = QTextBlockFormat()
        style_cr.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
        cursor.insertBlock(style_cr)

        cursor.movePosition(QTextCursor.Start)
        cursor = document.find('bbb')
        if cursor.isNull():
            qDebug('null')
        else:
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.insertBlock(style_cr)

        qDebug('Total {} blocks'.format(document.blockCount()))

        qDebug('{}'.format(document.toHtml()))
        return document

    def completeDocument(self,document):
        document = self.makeHeaderTable(document,self.styles['header.table'] )
        self.writeSeparator(document,single=False)
        document = self.writeExamData(document)
        return document

    def buildFakeHeaderInfo(self):
        from random import randint
        a = randint(3,20)
        b = randint(3,20)
        header_info = { 
            'west' : {
                'type': 'image',
                'data': dumpPixMapData(fileToPixMap(ARTWORK['left'])),
                'content': QUrl(ARTWORK['left']).toString()
            },
            'north' : {
                'type': 'image',
                'data': dumpPixMapData(fileToPixMap(ARTWORK['center'])),
                'content': QUrl(ARTWORK['center']).toString()
            },
            'south' : {
                'type': 'text',
                'content': "Lorem ipsum " * a
            },
            'east' : {
                'type': 'text',
                'content': "Lorem ipsum " * b
            }
        }
        return header_info

    def setupCell(self, table, row=0, col=0, centerH=True, centerV=True):
        cell = table.cellAt(row,col)
        cursor = cell.firstCursorPosition()
        
        if centerH:
            cursor.setBlockFormat(self.styles['centerH'])

        if centerV:
            cell.setFormat(self.styles['centerV'])
        return cursor,cell

    def imageResized(self, name, max_image_height, max_image_width):
        image = QImage(name)
        new_image_height = image.height() * max_image_width / image.width()
        image = image.scaled(max_image_width,new_image_height,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        if image.height() > max_image_height:
            new_image_width = image.width() * max_image_height / image.height()
            image = image.scaled(new_image_width,max_image_height,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        return image

    def makeHeaderTable(self, document, style, rows = header_table_rows, cols = header_table_cols, images = ARTWORK):

        max_image_width = (document.pageSize() / cols).width()
        max_image_height = (document.pageSize() / 6).height() # no big headers!

        first_element_row = 1
        first_element_col = 0
        num_rows = 1
        num_cols = cols

        coords = { 
            'west' : { 'y':0,'x':0 },
            'north': { 'y':0,'x':1 },
            'south': { 'y':1,'x':0 },
            'east': {'y':0,'x':2 }
        }

        cursor = QTextCursor(document)
        table = cursor.insertTable(rows,cols,self.styles['header.table'])
        table.mergeCells(first_element_row,first_element_col,num_rows,num_cols)

        positions = self.header_info.keys()
        for pos in positions:
            position = self.header_info.get(pos)
            coord = coords.get(pos)
            cursor,cell = self.setupCell(table,coord['y'],coord['x'])
            typeh = position.get('type')
            if typeh == 'text':
                cursor.insertText(position.get('content'), self.styles['text'])
            elif typeh == 'image':
                cursor.insertImage(self.imageResized(dataPixMapToImage(position.get('data')),max_image_height,max_image_width))
        self.writeSeparator(document)
        return document

    def makeTitleTable(self, document, rows, cols, cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        if cols == 2:
            table = cursor.insertTable(rows,cols,self.styles['title.table'])
        elif cols == 1:
            table = cursor.insertTable(rows,cols,self.styles['title.table.text'])
        return table
        
    def initCursor(self,document):
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.End)
        if cursor.hasSelection():
            cursor.clearSelection()
        return cursor

    def writeSeparator(self, document, cursor=None, number=None , single=False):
        if not cursor:
            cursor = self.initCursor(document)
        if single:
            style = self.styles['single']
        else:
            style = self.styles['double']
        cursor.insertBlock(style,self.styles['text'])
        txt = ""
        if number:
            txt = '{}'.format(number)
        cursor.insertText(txt)
        return cursor

    def setExamData(self,examData):
        self.examData = deepcopy(examData)

    def writeImage(self, document, image, cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        cursor.insertImage(image)

    def debug_document_blocklayout(self,document):
        ret=[]
        if not self.debug:
            return
        blockCount = document.blockCount()
        for i in range(blockCount):
            r = document.documentLayout().blockBoundingRect(document.findBlockByNumber(i))
            ret.append('Block #{} on ({},{}) with {}x{}'.format(i,r.x(),r.y(),r.width(),r.height()))
        qDebug("\n".join(ret))
        return ret

    def writePageBreak(self, document, cursorpos=None):
        cursor = QTextCursor(document)
        if not cursorpos:
            cursor = self.initCursor(document)
            cursor.insertBlock(self.styles['pagebreak'])
        else:
            cursor.setPosition(cursorpos)
            page1,pct1 = self.print_cursor_position_y(document,cursor)
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.blockFormat().setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
            cursor.insertBlock(self.styles['pagebreak'])
            page2,pct2 = self.print_cursor_position_y(document,cursor)
            if self.debug:
                qDebug('Break page: From {} {}% to {} {}%'.format(page1,pct1,page2,pct2))

    def writeLine(self, document, cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        if not self.splitWithFrame:
            cursor.insertFrame(QTextFrameFormat())
            return cursor
        pagenum,pct = self.print_cursor_position_y(document,cursor)

        cursor.insertFrame(self.styles['line'])
        ret = cursor.movePosition(QTextCursor.Down)
        return cursor

    def writeExamData(self,document):
        self.pagequestion = {}
        question_num = 0
        for row in self.examData:
            question_num += 1
            title = row.get('title')
            title = title.capitalize()
            typeq = row.get('type')
            title_pic = row.get('title_pic')
            cursor = self.initCursor(document)
            cursor_ini = cursor.position()
            pagestart,pct = self.print_cursor_position_y(document)
            if self.debug:
                qDebug("Starting question {} at page {} {}%".format(question_num,pagestart,pct))
            if title or title_pic:
                cols = 0
                if title:
                    cols += 1
                if title_pic:
                    cols += 1
                table = self.makeTitleTable(document, rows=1, cols=cols, cursor=cursor)
                if title:
                    cursor1,cell = self.setupCell(table,0,0,centerV=False)
                    if title_pic:
                        self.writeSeparator(document,cursor=cursor1,single=True)
                    self.writeTitle(document,title, cursor=cursor1,qnumber=question_num)
                if title_pic:
                    cursor2,cell = self.setupCell(table,0,1,centerV=False)
                    image = dataPixMapToImage(title_pic)
                    max_image_width = (document.pageSize() / 4).width()
                    image = image.scaledToWidth(max_image_width,Qt.SmoothTransformation)
                    self.writeImage(document, image, cursor=cursor2)
            self.writeSeparator(document,single=True)
            if self.debug:
                page,pct = self.print_cursor_position_y(document)
                qDebug("End title from question {} at page {} {}%, title={}...".format(question_num,pagestart,pct,title[:30]))

            self.writeSeparator(document,single=True)

            nlines = 0
            options = None
            if typeq == 'single_question':
                nlines = row.get('empty_lines')
            else:
                options = row.get('options')
                if typeq == 'test_question':
                    self.writeTest(document,options)
                elif typeq == 'join_activity':
                    self.writeJoinActivity(document,options)
                self.writeSeparator(document,single=False)

            for i in range(1,nlines+1):
                if self.debug:
                    self.writeSeparator(document,number=i)
                    page,pct = self.print_cursor_position_y(document)
                    qDebug('Space {} from question {} at page {} {}%'.format(i,question_num,page,pct))
                else:
                    self.writeSeparator(document)

            if self.debug:
                page,pct = self.print_cursor_position_y(document)
                qDebug("End options/lines from question {} at page {} {}%".format(question_num,page,pct))

            cursor_end = self.writeLine(document)
            cursor_end = cursor_end.position()
            pageend,pct  = self.print_cursor_position_y(document)
            self.pagequestion.setdefault(pagestart,[])
            self.pagequestion.setdefault(pageend,[])
            if pagestart == pageend:
                self.pagequestion[pagestart].append(question_num)
                self.last_cursor_ack = cursor_end
                if self.debug:
                    qDebug('Question {} write success until page {} {}%'.format(question_num,pageend,pct))
            else:
                if len(self.pagequestion[pagestart]) > 0:
                    if self.debug:
                        qDebug('Question {} goes next page, breaking page on last question'.format(question_num))
                    self.writePageBreak(document,cursor_ini)
                else:
                    if self.debug:
                        qDebug('Question {} sizes more than one page, skipping break, write sucess'.format(question_num))

            pageend,pct  = self.print_cursor_position_y(document)
            self.pagequestion[pageend].append(question_num)
            self.last_cursor_ack = cursor_end
            if self.debug:
                qDebug('End processing question {}, ended on page {} {}%'.format(question_num,pageend,pct))
        return document

    def writeTest(self, document, options, cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        
        rows = len(options)
        table = cursor.insertTable(rows,3,self.styles['option.table'])
        i=0
        tf = table.format()
        tf.setCellSpacing(mmToPixels(2,1200))
        table.setFormat(tf)
        for opt in options:
            text = opt.get('text1')
            text = text.capitalize()
            pic = opt.get('pic1')

            c,cell = self.setupCell(table,i,0,centerV=True,centerH=False)
            img = QImage(ICONS['option'])
            img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height(),Qt.SmoothTransformation)
            c.insertImage(img)
            if pic:
                c,cell = self.setupCell(table,i,1,centerV=True,centerH=False)
                img = dataPixMapToImage(pic)
                if img.isNull():
                    qDebug('Error: Invalid image detected')
                else:
                    img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*5,Qt.SmoothTransformation)
                    c.insertImage(img)
            if text:
                c,cell = self.setupCell(table,i,2,centerV=True,centerH=False)
                c.setCharFormat(self.styles['text'])
                c.insertText(text)

            i += 1
       
        return self.writeSeparator(document,single=True)

    def writeJoinActivity(self, document, options, cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        
        rows = len(options)
        table = cursor.insertTable(rows,7,self.styles['option.table.join'])
        tf = table.format()
        tf.setCellSpacing(mmToPixels(2,1200))
        table.setFormat(tf)
        i=0
        for opt in options:
            text1 = opt.get('text1')
            text1 = text1.capitalize()
            pic1 = opt.get('pic1')
            text2 = opt.get('text1')
            text2 = text2.capitalize()
            pic2 = opt.get('pic1')

            inc = 50
            if pic1:
                inc -= 10
            if pic2:
                inc -= 10
            if text1:
                inc -= 10
            if text2:
                inc -= 10
            separator = " " * inc

            space = " " * 3

            if text1:
                c,cell = self.setupCell(table,i,0,centerV=True,centerH=False)
                c.setCharFormat(self.styles['text'])
                c.insertText(text1+space)

            if pic1:
                c,cell = self.setupCell(table,i,1,centerV=False,centerH=False)
                img = dataPixMapToImage(pic1)
                if img.isNull():
                    qDebug('Error: Invalid image detected')
                else:
                    img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*5,Qt.SmoothTransformation)
                    c.insertImage(img)

            c,cell = self.setupCell(table,i,2,centerV=True,centerH=False)
            c.setCharFormat(self.styles['text'])
            c.insertText(space)
            img = QImage(ICONS['option'])
            img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*0.9,Qt.SmoothTransformation)
            c.insertImage(img)

            c,cell = self.setupCell(table,i,3,centerV=False,centerH=False)
            c.setCharFormat(self.styles['text'])
            c.insertText(separator)

            c,cell = self.setupCell(table,i,4,centerV=True,centerH=False)
            img = QImage(ICONS['option'])
            img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*0.9,Qt.SmoothTransformation)
            c.insertImage(img)
            c.setCharFormat(self.styles['text'])
            c.insertText(space)

            if pic2:
                c,cell = self.setupCell(table,i,5,centerV=False,centerH=False)
                img = dataPixMapToImage(pic2)
                if img.isNull():
                    qDebug('Error: Invalid image detected')
                else:
                    img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*5,Qt.SmoothTransformation)
                    c.insertImage(img)

            if text2:
                c,cell = self.setupCell(table,i,6,centerV=True,centerH=False)
                c.setCharFormat(self.styles['text'])
                c.insertText(space+text2)

            i += 1

        return self.writeSeparator(document,single=True)

    def writeTitle(self,document,text, cursor=None, qnumber=None):
        if document and text:
            if not cursor:
                cursor = self.initCursor(document)
            cursor.insertBlock(self.styles['body'],self.styles['text'])
            if qnumber:
                cursor.insertText('Question {}: '.format(qnumber),self.styles['text.bold'])
            cursor.insertText(text,self.styles['text'])

    def validateHeader(self,header):
        fake = None
        if USE_FAKE_HEADER:
            fake = self.buildFakeHeaderInfo()

        if not header or not isinstance(header,dict):
            if fake:
                return fake
            header = {'west':{},'north':{},'east':{},'south':{}}

        ks = ['west','north','east','south']
        for k in ks:
            if k not in header.keys():
                if fake:
                    header[k] = deepcopy(fake[k])
                    continue
                header.setdefault(k,{})

            if not isinstance(header[k],dict):
                if fake:
                    header[k] = deepcopy(fake[k])
                    continue
                header[k]={}

            header[k].setdefault('type','text')
            if header[k]['type'] not in ['image','text']:
                if fake:
                    header[k] = deepcopy(fake[k])
                    continue
                header[k]['type'] = 'text'

            if header[k]['type'] == 'image':
                if not header[k].get('data'):
                    if fake:
                        header[k] = deepcopy(fake[k])
                        continue
                    header[k]['type'] = 'text'

            if header[k]['type'] == 'text':
                header[k].setdefault('content','')

        return header

    def setHeaderInfo(self,header_info):
            self.header_info = deepcopy(self.validateHeader(header_info))

# class BData(QTextBlockUserData):
#     def __init__(self,data=None):
#         super().__init__()
#         self.data = data

class ExamDocument(QTextDocument):
    def __init__(self,*args,**kwargs):
        self.headersSize = 16
        self.resolution = None
        super().__init__(*args,**kwargs)

    def setHeadersSize(self, value):
        self.headersSize = value

    def setPage(self,pageSize=None,printer=None):
        if not pageSize:
            if printer:
                self.resolution = printer.resolution()
                pageSize = printer.pageRect().size()
                if self.headersSize:
                    pageSize.setHeight(pageSize.height()-mmToPixels(self.headersSize,resolution=self.resolution))
            else:
                return
        self.setPageSize(pageSize)

    def printPageWithHeaders(self,index,painter,document,body,printer,header="HEADER",footer="FOOTER",framed=True):

        fontHeaders = QFont('courier',self.headersSize,QFont.Black)

        printer_height = printer.height()
        paper_height = body.height()

        offset_document = (index-1) * paper_height

        free_space = printer_height - paper_height
        header_height = free_space / 2
        footer_height = free_space / 2

        # header rect
        # Coordinates into one page
        headerPageRect = QRectF(0,0, printer.width(), header_height)
        # text rect
        # Coordinates into one page
        # textPageRect = QRectF(0, header_height, printer.width(), body.height())
        # view rect
        # Coordinates into full document
        viewRect = QRectF(QPointF(0,offset_document), body.size())
        # footer rect
        # Coordinates into one page
        footerPageRect = QRectF(0,printer_height-footer_height, printer.width(), header_height)

        offset_line = mmToPixels(2,resolution=printer.resolution())

        pen = painter.pen()
        pen.setColor(Qt.black)

        painter.save()        
        painter.setRenderHint(QPainter.TextAntialiasing,True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing,False)

        offset_header = 0

        if header:
            painter.setPen(pen)
            painter.setFont(fontHeaders)
            painter.drawText(headerPageRect,Qt.AlignRight, header)
            if framed:
                pen.setWidth(5)
                painter.setPen(pen)
                painter.drawLine(0,header_height-offset_line,printer.width(),header_height-offset_line)
            offset_header = header_height
        
        offset_header = - offset_document + offset_header
        painter.translate(0, offset_header)
        
        layout = document.documentLayout()
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.clip = viewRect
        ctx.palette.setColor(QPalette.Text,Qt.black)
        layout.draw(painter,ctx)
        painter.restore()
        
        if footer:
            painter.save()
            painter.setRenderHint(QPainter.TextAntialiasing,True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing,False)
            pen = painter.pen()
            pen.setWidth(5)
            pen.setColor(Qt.black)
            painter.setPen(pen)
            if framed:
                painter.drawLine(0,paper_height+header_height-offset_line,printer.width(),paper_height+header_height-offset_line)
            painter.setFont(fontHeaders)
            painter.drawText(footerPageRect,Qt.AlignRight, footer)
            painter.restore()

    def printExamModel(self,printer,model="",numbered=True,framed=True):
        p = QPainter(printer)       
        self.setPage(printer=printer)
        body = QRectF(QPointF(0,0),self.pageSize())
        for i in range(self.pageCount()):
            if i != 0:
                printer.newPage()
            footer=""
            if numbered:
                footer = "{}/{}".format(i+1,self.pageCount())
            self.printPageWithHeaders(i+1,p,self,body,printer,header=model,footer=footer,framed=framed)

# class MyPrinter(QPrinter):
#     def __init__(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
#     def paintRequested(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
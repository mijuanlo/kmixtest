from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Util import mmToPixels, pixelsToMm, picaToPixels, marginsToString, print_document_data, print_preview_data, print_printer_data, loadPixMapData, dumpPixMapData, fileToPixMap, dataPixMapToImage, timed
from .PreviewPrinter import previewPrinter
from .Config import _, ARTWORK, ICONS

from copy import deepcopy
import os.path

USE_FAKE_HEADER = True

# Helper class with pdf stuff related things
class helperPDF():

    header_table_cols = 3
    header_table_rows = 3

    def __init__(self, parent=None, debug=False):
        self.debug = False or debug
        self.parent = parent
        if self.parent and getattr(parent,'debug',None):
            self.debug = getattr(parent,'debug',None)
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
        self.examData = None
        if self.debug:
            self.headerWithFrame = True
            self.splitWithFrame = True

    def setCustomizations(self,numberedPages, splitWithFrames, headerWithFrame):
        self.splitWithFrame = splitWithFrame
        self.numberedPages = numberedPages
        self.headerWithFrame = headerWithFrame

    @timed
    def initPrinter(self, printer=None, resolution=QPrinter.HighResolution, margins=None, orientation=None):
        if not resolution:
            if not self.resolution_type:
                self.resolution_type = QPrinter.HighResolution
            # resolution = QPrinter(self.resolution_type).resolution()
        if isinstance(resolution,QPrinter.PrinterMode):
            default_printer = QPrinter(resolution)
            resolution = default_printer.resolution()
        else:
            default_printer = QPrinter()
            default_printer.setResolution(resolution)
        self.dpi = resolution
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
                qDebug("{} {}".format(_('Setting margins to'),marginsToString(margins)))
            current_layout.setMargins(margins)
            changed_layout = True
        else:
            self.pageMargins = current_layout.margins()
        
        if orientation is not None and isinstance(orientation, QPageLayout.Orientation):
            if self.debug:
                qDebug("{} {}".format(_('Setting orientation to'),orientation.name.decode()))
            current_layout.setOrientation(orientation)
            changed_layout = True

        if changed_layout:
            printer.setPageLayout(current_layout)
        # PaperToScreen = int( resolution / QPrinter(QPrinter.ScreenResolution).resolution() )
        PaperToScreen = int( resolution / 96 )
        self.constPaperScreen = PaperToScreen
        if self.debug:
            qDebug("{}: {}".format(_('Setting constant'),int(self.constPaperScreen)))

        relTextToA4 = int(self.printer.pageSizeMM().width()/210.0)
        self.relTextToA4 = relTextToA4
        if self.debug:
            qDebug("{}: {}".format(_('Setting text multiplier size'),relTextToA4))
        return printer, resolution, PaperToScreen, current_layout

    @timed
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

    @timed
    def initWidget(self, parent=None, printer=None,fn=None):
        widget = previewPrinter(parent=parent,printer=printer)
        widget.paintRequested.connect(fn)
        return widget 

    @timed
    def initSystem(self,printer=None,filename=None):
        self.last_cursor_ack = None
        self.last_page_ack = 1
        if printer:
            self.printer = printer
        if not self.printer:
            self.printer, self.dpi, self.constPaperScreen, self.layout = self.initPrinter(printer=self.printer, resolution=self.resolution_type, margins=self.pageMargins)
        if not self.preview:
            self.printer.setOutputFormat(QPrinter.PdfFormat)
            if filename:
                self.printer.setOutputFileName(filename)
            else:
                self.printer.setOutputFileName('out.pdf')

    @timed
    def openWidget(self,answermode=False):
        self.preview = True
        self.document = self.completeDocument(answermode)
        self.widget = self.initWidget(parent=self, printer=self.printer, fn=self.paintRequest )
        self.widget.exec_()

    @timed
    def writePDF(self,filename=None,answermode=False):
        self.preview = False
        self.document = self.completeDocument(answermode)
        dialog = QMessageBox()
        hspacer = QSpacerItem(300,0,QSizePolicy.Minimum,QSizePolicy.Expanding)
        dialog.setProperty('icon',QMessageBox.Information)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setText("{}".format(_('Pdf file generated')))
        self.paintRequest(filename=filename)
        dialog.setInformativeText(filename)
        dialog.setStyleSheet('QMessageBox QLabel#qt_msgbox_label{ font-size: 12pt; } QMessageBox QLabel#qt_msgbox_informativelabel{ font-size: 10pt; }')
        dialog.layout().addItem(hspacer,dialog.layout().rowCount(),0,1,dialog.layout().columnCount())
        dialog.exec_()

    @timed
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
        styles[x].setCellPadding(mmToPixels(5,resolution=resolution))
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
            qDebug("{}: {}".format(_('Using text multiplier size'),int(self.relTextToA4)))
        
        # styles['defaultfont'] = QFont("Times",10 * self.constPaperScreen * self.relTextToA4)
        # styles['bigfont'] = QFont("Times",30 * self.constPaperScreen * self.relTextToA4)

        styles['defaultfont'] = QFont("Times", picaToPixels(10))
        styles['bigfont'] = QFont("Times", picaToPixels(30))
        styles['answer_ok'] = QFont("Times", picaToPixels(14),QFont.Bold)
        styles['answer_fail'] = styles['defaultfont']
        styles['answer_fail'].setWeight(QFont.Light)

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
    def paintRequest(self, printer=None, filename=None):
        if self.debug:
            qDebug("***** {} ! *****".format(_('Repaint Event')))

        self.initSystem(printer,filename)
        if self.debug:        
            # print_document_data(self.document)
            print_printer_data(self.printer)

        #self.document = self.completeDocument(answermode)
        #self.document = self.makeTestDocument(self.document)
        self.document.printExamModel(self.printer,numbered=self.numberedPages,framed=self.headerWithFrame)

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

    @timed
    def completeDocument(self, answermode=False):
        document = self.initDocument(printer = self.printer)
        document = self.writeExamData(document, answermode)
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
        sw = max_image_width / image.width()
        sh = max_image_height / image.height()
        s = min(sw,sh)
        return image.scaled(s*image.width(),s*image.height(),Qt.KeepAspectRatio,Qt.SmoothTransformation)

    def makeHeaderTable(self, document=None, headerdata=None, answermode=False):
        printer = self.printer
        config = self.headerData.get('config')
        cursor = self.initCursor(document)
        tableformat = QTextTableFormat()
        configborder = None
        bordersize = 2  # pixels
        paddingsize = 1  # mm
        if config:
            configborder = config.get('border')
        if configborder:
            tableformat.setBorderStyle(QTextTableFormat.BorderStyle_Solid)
            tableformat.setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
            tableformat.setBorder(bordersize)
        elif configborder is False:
            tableformat.setBorderStyle(QTextTableFormat.BorderStyle_None)
        else:
            tableformat.setBorderStyle(QTextTableFormat.BorderStyle_Solid)
            tableformat.setBorderBrush(QBrush(Qt.black,Qt.SolidPattern))
            tableformat.setBorder(bordersize)
        tableformat.setMargin(0.0)
        tableformat.setCellSpacing(0.0)
        paddingsize = mmToPixels(paddingsize,resolution=document.resolution)
        tableformat.setCellPadding(paddingsize)
        nrows = headerdata.get('nrows')
        ncols = headerdata.get('ncols')
        tablecolumnsize = document.pageSize().width() / ncols - (ncols + 1) * bordersize
        qt_tablecolumnsize = QTextLength(QTextLength.FixedLength,tablecolumnsize)
        tableformat.setColumnWidthConstraints([qt_tablecolumnsize] * ncols)
        table = cursor.insertTable(nrows,headerdata.get('ncols'),tableformat)
        joins = headerdata.get('joins')
        if joins:
            for k,v in joins.items():
                y,x = [int(x) for x in k.split('_')]
                sy,sx = v
                table.mergeCells(y,x,sy,sx)
        content = headerdata.get('content')
        if content:
            for k,v in content.items():
                y,x = [ int(x) for x in k.split('_') ]
                align = v.get('align')
                pix = v.get('pix')
                txt = v.get('txt')
                if txt:
                    isField = True if '_@[' in txt.get('value') and ']@_' in txt.get('value') else False
                if align:
                    if align == 'left':
                        align = Qt.AlignLeft|Qt.AlignVCenter
                    elif align == 'right':
                        align = Qt.AlignRight|Qt.AlignVCenter
                    else:
                        align = Qt.AlignCenter
                else:
                    align = Qt.AlignCenter
                cell = table.cellAt(y,x)
                cursor = cell.firstCursorPosition()
                blockformat = QTextBlockFormat()
                blockformat.setAlignment(align)
                cursor.setBlockFormat(blockformat)
                charformat = QTextCharFormat()
                charformat.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)
                cell.setFormat(charformat)
                if txt:
                    if not isField:
                        cursor.insertText(txt.get('show'),self.styles['text'])
                    else:
                        txt = txt.get('show')
                        cursor.insertBlock(blockformat,self.styles['text.bold'])
                        width = tablecolumnsize*cell.columnSpan()-2*paddingsize
                        fm = QFontMetrics(self.styles['text.bold'].font())
                        if bordersize:
                            sub = ' '
                        else:
                            sub = '_'
                        cursor.insertText("{}:{}".format(txt,sub*int((width-fm.size(Qt.TextSingleLine,txt+':').width())/fm.size(Qt.TextSingleLine,sub).width())))
                if pix:
                    pix = dataPixMapToImage(pix)
                    max_image_height = ( tablecolumnsize / pix.width() ) * pix.height()
                    pix = self.imageResized(pix,max_image_height*cell.rowSpan()-2*paddingsize,tablecolumnsize*cell.columnSpan()-2*paddingsize)
                    cursor.insertImage(pix)
                    
        return document
        
       
        cursor,cell = self.setupCell(table,2,1,centerH=False,centerV=True)
        cursor.insertText('Name',self.styles['text.bold'])
        cursor,cell = self.setupCell(table,2,2,centerH=False,centerV=True)
        cursor.insertText('Group',self.styles['text.bold'])
        self.writeSeparator(document, single=True)
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
            ret.append('{} #{} {} ({},{}) {} {}x{}'.format(_('Block'),i,_('on'),r.x(),r.y(),_('with'),r.width(),r.height()))
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
                qDebug('{}: {} {} {}% {} {} {}%'.format(_('Break page'),_('From'),page1,pct1,_('to'),page2,pct2))

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

    @timed
    def writeExamData(self,document,answermode=False):
        if not self.examData:
            return document
        for model in self.examData:
            if model[0] == '_':
                continue
            document.setInitModel(model)
            if self.headerData:
                nrows = self.headerData.get('nrows')
                ncols = self.headerData.get('ncols')
                spans = self.headerData.get('joins')
                content = self.headerData.get('content')
                #self.styles['header.table'] = self.makeTableStyle(rows=nrows, cols=ncols, spans=spans, content=content, border=True)
                document = self.makeHeaderTable(document=document,headerdata=self.headerData,answermode=answermode)
            # if not answermode:
            #     document = self.writeTitleName(document)
            # else:
            self.writeSeparator(document,single=True)    
            self.writeSeparator(document,single=True)
            self.writeSeparator(document,single=True)
            data = self.examData[model]
            self.pagequestion = {}
            question_num = 0
            for row in data:
                question_num += 1
                title = row.get('title')
                title = title.capitalize()
                typeq = row.get('type')
                title_pic = row.get('title_pic')
                cursor = self.initCursor(document)
                cursor_ini = cursor.position()
                pagestart,pct = self.print_cursor_position_y(document)
                if self.debug:
                    qDebug("{} {} {} {} {}%".format(_("Starting question"),question_num,_('at page'),pagestart,pct))
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
                        if answermode:
                            self.writeTitle(document,title, cursor=cursor1,qnumber=question_num, html=True)
                        else:
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
                    qDebug("{} {} {} {} {}%, {}={}...".format(_('End title from question'),question_num,_('at page'),pagestart,pct,_('title'),title[:30]))

                self.writeSeparator(document,single=True)

                nlines = 0
                options = None
                if typeq == 'single_question':
                    nlines = row.get('empty_lines')
                else:
                    options = row.get('options')
                    if typeq == 'test_question':
                        if answermode:
                            self.writeTest(document,options, html=True)
                        else:
                            self.writeTest(document,options, html=False)
                    elif typeq == 'join_activity':
                        if answermode:
                            row_mapping = row.get('join_mapping')
                            self.writeJoinActivity(document,options, html=True, mapping=row_mapping)
                        else:
                            self.writeJoinActivity(document,options, html=False)
                    self.writeSeparator(document,single=False)

                for i in range(1,nlines+1):
                    if self.debug:
                        self.writeSeparator(document,number=i)
                        page,pct = self.print_cursor_position_y(document)
                        qDebug('{} {} {} {} {} {} {}%'.format(_('Space'),i,_('from question'),question_num,_('at page'),page,pct))
                    else:
                        self.writeSeparator(document)

                if self.debug:
                    page,pct = self.print_cursor_position_y(document)
                    qDebug("{} {} {} {} {} {}%".format(_('End options/lines'),_('from question'),question_num,_('at page'),page,pct))

                cursor_end = self.writeLine(document)
                cursor_end = cursor_end.position()
                pageend,pct  = self.print_cursor_position_y(document)
                self.pagequestion.setdefault(pagestart,[])
                self.pagequestion.setdefault(pageend,[])
                if pagestart == pageend:
                    self.pagequestion[pagestart].append(question_num)
                    self.last_cursor_ack = cursor_end
                    if self.debug:
                        qDebug('{} {} {} {} {}%'.format(_('Question'),question_num,_('write success until page'),pageend,pct))
                else:
                    if len(self.pagequestion[pagestart]) > 0:
                        if self.debug:
                            qDebug('{} {} {}'.format(_('Question'),question_num,_('goes next page, breaking page on last question')))
                        self.writePageBreak(document,cursor_ini)
                    else:
                        if self.debug:
                            qDebug('{} {} {}'.format(_('Question'),question_num,_('sizes more than one page, skipping break, write sucess')))

                pageend,pct  = self.print_cursor_position_y(document)
                self.pagequestion[pageend].append(question_num)
                self.last_cursor_ack = cursor_end
                if self.debug:
                    qDebug('{} {}, {} {} {}%'.format(_('End processing question'),question_num,_('ended on page'),pageend,pct))
        document.setEndModel(breakPage=False)
        return document

    def writeTest(self, document, options, cursor=None, html=False, color='red'):
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
            is_valid = opt.get('valid')

            iconbox = ICONS['option']
            size = None
            family = None
            color = None
            weight = None
            style = 'defaultfont'
            if html:
                if is_valid:
                    style = 'answer_ok'
                    color = 'darkgreen'
                    iconbox = ICONS['boxok']
                    family = self.styles[style].family()
                    size = int(self.styles[style].pointSize())
                    weight = int(self.styles[style].weight()*8)
                    decoration = 'none'
                else:
                    style = 'answer_fail'
                    color = 'darksalmon'
                    iconbox = ICONS['boxfail']
                    family = self.styles[style].family()
                    size = int(self.styles[style].pointSize())
                    weight = int(self.styles[style].weight()*8)
                    decoration = 'line-through'

            c,cell = self.setupCell(table,i,0,centerV=True,centerH=False)
            img = QImage(iconbox)
            img = img.scaledToHeight(QFontMetrics(self.styles[style]).height(),Qt.SmoothTransformation)
            c.insertImage(img)
            if pic:
                c,cell = self.setupCell(table,i,1,centerV=True,centerH=False)
                img = dataPixMapToImage(pic)
                if img.isNull():
                    qDebug(_('Error: Invalid image detected'))
                else:
                    img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*5,Qt.SmoothTransformation)
                    c.insertImage(img)
            if text:
                c,cell = self.setupCell(table,i,2,centerV=True,centerH=False)
                if html:
                    c.insertHtml('<span style="text-decoration:{};font-size:{}pt;font-family:{};color:{};font-weight:{};">{}</span>'.format(decoration,size,family,color,weight,text))
                else:
                    c.setCharFormat(self.styles['text'])
                    c.insertText(text)
            i += 1
       
        return self.writeSeparator(document,single=True)

    def writeJoinActivity(self, document, options, cursor=None, html=False, color='red', mapping=None):
        if not cursor:
            cursor = self.initCursor(document)
        
        rows = len(options)
        table = cursor.insertTable(rows,7,self.styles['option.table.join'])
        tf = table.format()
        tf.setCellSpacing(mmToPixels(2,1200))
        table.setFormat(tf)
        i=-1
        for opt in options:
            i += 1
            text1 = opt.get('text1')
            text1 = text1.capitalize()
            pic1 = opt.get('pic1')
            text2 = opt.get('text2')
            text2 = text2.capitalize()
            pic2 = opt.get('pic2')

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
                if html:
                    family = self.styles['text'].fontFamily()
                    weight = int(self.styles['text'].fontWeight()*8)
                    size = int(self.styles['text'].fontPointSize())
                    color = 'dimgray'
                    c.insertHtml('<span style="font-size:{}pt;font-family:{};color:{};font-weight:{};">{}</span>'.format(size,family,color,weight,text1+space))
                else:
                    c.setCharFormat(self.styles['text'])
                    c.insertText(text1+space)

            if pic1:
                c,cell = self.setupCell(table,i,1,centerV=False,centerH=False)
                img = dataPixMapToImage(pic1)
                if img.isNull():
                    qDebug(_('Error: Invalid image detected'))
                else:
                    img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*5,Qt.SmoothTransformation)
                    c.insertImage(img)

            c,cell = self.setupCell(table,i,2,centerV=True,centerH=False)
            if html and mapping:
                text = chr(i+65)
                family = self.styles['answer_ok'].family()
                weight = int(self.styles['answer_ok'].weight()*8)
                size = int(self.styles['answer_ok'].pointSize())
                color = 'black'
                c.insertHtml('<span style="font-size:{}pt;font-family:{};color:{};font-weight:{};"> {}</span>'.format(size,family,color,weight,text))
            else:
                c.setCharFormat(self.styles['text'])
                c.insertText(space)
                img = QImage(ICONS['option'])
                img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*0.9,Qt.SmoothTransformation)
                c.insertImage(img)

            c,cell = self.setupCell(table,i,3,centerV=False,centerH=False)
            c.setCharFormat(self.styles['text'])
            c.insertText(separator)

            c,cell = self.setupCell(table,i,4,centerV=True,centerH=False)
            if html and mapping:
                text = chr(mapping[i]+65)
                family = self.styles['answer_ok'].family()
                weight = int(self.styles['answer_ok'].weight()*8)
                size = int(self.styles['answer_ok'].pointSize())
                color = 'black'
                c.insertHtml('<span style="font-size:{}pt;font-family:{};color:{};font-weight:{};">{} </span>'.format(size,family,color,weight,text))
            else:
                img = QImage(ICONS['option'])
                img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*0.9,Qt.SmoothTransformation)
                c.insertImage(img)
                c.setCharFormat(self.styles['text'])
                c.insertText(space)

            if pic2:
                c,cell = self.setupCell(table,i,5,centerV=False,centerH=False)
                img = dataPixMapToImage(pic2)
                if img.isNull():
                    qDebug(_('Error: Invalid image detected'))
                else:
                    img = img.scaledToHeight(QFontMetrics(self.styles['defaultfont']).height()*5,Qt.SmoothTransformation)
                    c.insertImage(img)

            if text2:
                c,cell = self.setupCell(table,i,6,centerV=True,centerH=False)
                if html:
                    family = self.styles['text'].fontFamily()
                    weight = int(self.styles['text'].fontWeight()*8)
                    size = int(self.styles['text'].fontPointSize())
                    color = 'dimgray'
                    c.insertHtml('<span style="font-size:{}pt;font-family:{};color:{};font-weight:{};">{}</span>'.format(size,family,color,weight,space+text2))
                else:
                    c.setCharFormat(self.styles['text'])
                    c.insertText(space+text2)

        return self.writeSeparator(document,single=True)

    def writeTitleName(self,document,cursor=None):
        if not cursor:
            cursor = self.initCursor(document)
        cursor.insertBlock(self.styles['body'],self.styles['text.bold'])
        width = document.idealWidth()
        fm = QFontMetrics(self.styles['text.bold'].font())
        cursor.insertText("{}: {}".format(_('Name'),'_'*int((width-fm.size(Qt.TextSingleLine,_('Name')+':').width())/fm.size(Qt.TextSingleLine,'_').width())))
        return document

    def writeTitle(self,document,text, cursor=None, qnumber=None, html=False, color='red'):
        if document and text:
            if not cursor:
                cursor = self.initCursor(document)
            cursor.insertBlock(self.styles['body'],self.styles['text'])
            family = self.styles['text'].fontFamily()
            weight = int(self.styles['text'].fontWeight()*8)
            size = int(self.styles['text'].fontPointSize())
            bfamily = self.styles['text.bold'].fontFamily()
            bweight = int(self.styles['text.bold'].fontWeight()*8)
            bsize = int(self.styles['text.bold'].fontPointSize())
            if qnumber:
                if html:
                    color = 'dimgray'
                    cursor.insertHtml('<span style="font-size:{}pt;font-family:{};color:{};font-weight:{};">{} {}: </span>'.format(bsize,bfamily,color,900,_('Question'),qnumber))
                else:
                    cursor.insertText('{} {}: '.format(_('Question'),qnumber),self.styles['text.bold'])
            if html:
                color = 'lightgray'
                cursor.insertHtml('<span style="font-size:{}pt;font-family:{};color:{};font-weight:{};">{}</span>'.format(size,family,color,weight,text))
            else:
                cursor.insertText(text,self.styles['text'])

    def setHeaderInfo(self,headerData):
            self.headerData = deepcopy(headerData)

# class BData(QTextBlockUserData):
#     def __init__(self,data=None):
#         super().__init__()
#         self.data = data

class ExamDocument(QTextDocument):
    def __init__(self,*args,**kwargs):
        self.headersSize = 16
        self.resolution = None
        self.modelOrder = []
        self.models = {}
        super().__init__(*args,**kwargs)

    def setHeadersSize(self, value):
        self.headersSize = value

    def setInitModel(self,model):
        self.setEndModel()
        self.modelOrder.append(model)
        self.models.setdefault(model,{'ini': self.pageCount(), 'end':None, 'started': True})

    def setEndModel(self,breakPage=True):
        keys = self.models.keys()
        if len(self.modelOrder) != len(keys) or len(keys) < 1:
            return None
        last = self.modelOrder[-1]
        if last not in keys:
            raise ValueError()
        if self.models[last].get('started'):
            self.models[last]['started'] = False
            self.models[last]['end'] = self.pageCount()
            if breakPage:
                cursor = QTextCursor(self)
                cursor.movePosition(QTextCursor.End)
                pb = QTextBlockFormat()
                pb.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
                cursor.insertBlock(pb)

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

    @timed
    def printExamModel(self,printer,numbered=True,framed=True):
        headermap = {}
        footermap = {}
        footer = ''
        header = ''
        for modelname, infomodel in self.models.items():
            counter = 1
            for i in range(infomodel.get('ini'),infomodel.get('end')+1):
                headermap.setdefault(i,modelname)
                footermap.setdefault(i,counter)
                counter += 1
        p = QPainter(printer)
        self.setPage(printer=printer)
        body = QRectF(QPointF(0,0),self.pageSize())
        for i in range(self.pageCount()):
            if i != 0:
                printer.newPage()
            if headermap:
                header = str(headermap.get(i+1))
                if numbered:
                    info = self.models.get(headermap.get(i+1))
                    footer = "{}/{}".format(footermap.get(i+1),info.get('end')-info.get('ini')+1)
            self.printPageWithHeaders(i+1,p,self,body,printer,header=header,footer=footer,framed=framed)

# class MyPrinter(QPrinter):
#     def __init__(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
#     def paintRequested(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
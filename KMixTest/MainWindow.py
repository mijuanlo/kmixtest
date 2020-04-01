# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 5.14.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
    QRadialGradient)
from PySide2.QtWidgets import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_6 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.scrollAreaQuestions = QScrollArea(self.centralwidget)
        self.scrollAreaQuestions.setObjectName(u"scrollAreaQuestions")
        self.scrollAreaQuestions.setWidgetResizable(True)
        self.scrollAreaContentsQuestions = QWidget()
        self.scrollAreaContentsQuestions.setObjectName(u"scrollAreaContentsQuestions")
        self.scrollAreaContentsQuestions.setGeometry(QRect(0, 0, 386, 475))
        self.verticalLayout = QVBoxLayout(self.scrollAreaContentsQuestions)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tableWidgetQuestions = QTableWidget(self.scrollAreaContentsQuestions)
        if (self.tableWidgetQuestions.columnCount() < 4):
            self.tableWidgetQuestions.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidgetQuestions.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidgetQuestions.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidgetQuestions.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidgetQuestions.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.tableWidgetQuestions.setObjectName(u"tableWidgetQuestions")
        self.tableWidgetQuestions.setFocusPolicy(Qt.NoFocus)
        self.tableWidgetQuestions.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidgetQuestions.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidgetQuestions.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tableWidgetQuestions.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidgetQuestions.setShowGrid(False)
        self.tableWidgetQuestions.setColumnCount(4)
        self.tableWidgetQuestions.horizontalHeader().setVisible(True)
        self.tableWidgetQuestions.horizontalHeader().setMinimumSectionSize(20)
        self.tableWidgetQuestions.horizontalHeader().setDefaultSectionSize(20)
        self.tableWidgetQuestions.horizontalHeader().setStretchLastSection(True)
        self.tableWidgetQuestions.verticalHeader().setVisible(True)

        self.verticalLayout.addWidget(self.tableWidgetQuestions)

        self.scrollAreaQuestions.setWidget(self.scrollAreaContentsQuestions)

        self.horizontalLayout_2.addWidget(self.scrollAreaQuestions)

        self.scrollAreaAnswers = QScrollArea(self.centralwidget)
        self.scrollAreaAnswers.setObjectName(u"scrollAreaAnswers")
        self.scrollAreaAnswers.setWidgetResizable(True)
        self.scrollAreaContentsAnswers = QWidget()
        self.scrollAreaContentsAnswers.setObjectName(u"scrollAreaContentsAnswers")
        self.scrollAreaContentsAnswers.setGeometry(QRect(0, 0, 386, 475))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaContentsAnswers)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gridEdition = QGridLayout()
        self.gridEdition.setObjectName(u"gridEdition")

        self.verticalLayout_3.addLayout(self.gridEdition)

        self.scrollAreaAnswers.setWidget(self.scrollAreaContentsAnswers)

        self.horizontalLayout_2.addWidget(self.scrollAreaAnswers)


        self.verticalLayout_6.addLayout(self.horizontalLayout_2)

        self.previewButton = QPushButton(self.centralwidget)
        self.previewButton.setObjectName(u"previewButton")
        sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.previewButton.sizePolicy().hasHeightForWidth())
        self.previewButton.setSizePolicy(sizePolicy)
        self.previewButton.setMaximumSize(QSize(16777215, 16777215))

        self.verticalLayout_6.addWidget(self.previewButton)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 30))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"KMixTest", None))
        ___qtablewidgetitem = self.tableWidgetQuestions.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Order", None));
        ___qtablewidgetitem1 = self.tableWidgetQuestions.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Fixed", None));
        ___qtablewidgetitem2 = self.tableWidgetQuestions.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Linked", None));
        ___qtablewidgetitem3 = self.tableWidgetQuestions.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Title", None));
        self.previewButton.setText(QCoreApplication.translate("MainWindow", u"Preview", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi


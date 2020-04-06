# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'headerForm.ui'
##
## Created by: Qt User Interface Compiler version 5.14.0
## uic -g python --idbased --tr _ lib/headerForm.ui > KMixTest/Ui_headerForm.py
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
    QRadialGradient)
from PySide2.QtWidgets import *

class Ui_headerForm(object):
    def setupUi(self, headerForm):
        if headerForm.objectName():
            headerForm.setObjectName(u"headerForm")
        headerForm.setWindowModality(Qt.ApplicationModal)
        headerForm.resize(640, 505)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(headerForm.sizePolicy().hasHeightForWidth())
        headerForm.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(headerForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.iconInfoLabel = QLabel(headerForm)
        self.iconInfoLabel.setObjectName(u"iconInfoLabel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.iconInfoLabel.sizePolicy().hasHeightForWidth())
        self.iconInfoLabel.setSizePolicy(sizePolicy1)
        self.iconInfoLabel.setMinimumSize(QSize(0, 0))
        self.iconInfoLabel.setBaseSize(QSize(20, 0))

        self.horizontalLayout_7.addWidget(self.iconInfoLabel)

        self.infoLabel = QLabel(headerForm)
        self.infoLabel.setObjectName(u"infoLabel")

        self.horizontalLayout_7.addWidget(self.infoLabel)


        self.gridLayout.addLayout(self.horizontalLayout_7, 1, 0, 1, 1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.headerTable = QTableWidget(headerForm)
        if (self.headerTable.columnCount() < 1):
            self.headerTable.setColumnCount(1)
        self.headerTable.setObjectName(u"headerTable")
        sizePolicy.setHeightForWidth(self.headerTable.sizePolicy().hasHeightForWidth())
        self.headerTable.setSizePolicy(sizePolicy)
        self.headerTable.setColumnCount(1)
        self.headerTable.horizontalHeader().setVisible(False)
        self.headerTable.horizontalHeader().setCascadingSectionResizes(False)
        self.headerTable.horizontalHeader().setDefaultSectionSize(153)
        self.headerTable.horizontalHeader().setHighlightSections(False)
        self.headerTable.horizontalHeader().setStretchLastSection(False)
        self.headerTable.verticalHeader().setVisible(False)
        self.headerTable.verticalHeader().setDefaultSectionSize(86)
        self.headerTable.verticalHeader().setHighlightSections(False)

        self.horizontalLayout_4.addWidget(self.headerTable)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.nColumnLabel = QLabel(headerForm)
        self.nColumnLabel.setObjectName(u"nColumnLabel")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.nColumnLabel.sizePolicy().hasHeightForWidth())
        self.nColumnLabel.setSizePolicy(sizePolicy2)
        self.nColumnLabel.setIndent(6)

        self.verticalLayout.addWidget(self.nColumnLabel, 0, Qt.AlignLeft)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetFixedSize)
        self.columnSlider = QSlider(headerForm)
        self.columnSlider.setObjectName(u"columnSlider")
        sizePolicy2.setHeightForWidth(self.columnSlider.sizePolicy().hasHeightForWidth())
        self.columnSlider.setSizePolicy(sizePolicy2)
        self.columnSlider.setMinimum(1)
        self.columnSlider.setMaximum(5)
        self.columnSlider.setPageStep(1)
        self.columnSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_2.addWidget(self.columnSlider)

        self.valueNColumnSlider = QLabel(headerForm)
        self.valueNColumnSlider.setObjectName(u"valueNColumnSlider")
        sizePolicy2.setHeightForWidth(self.valueNColumnSlider.sizePolicy().hasHeightForWidth())
        self.valueNColumnSlider.setSizePolicy(sizePolicy2)

        self.horizontalLayout_2.addWidget(self.valueNColumnSlider)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.nRowLabel = QLabel(headerForm)
        self.nRowLabel.setObjectName(u"nRowLabel")
        sizePolicy2.setHeightForWidth(self.nRowLabel.sizePolicy().hasHeightForWidth())
        self.nRowLabel.setSizePolicy(sizePolicy2)
        self.nRowLabel.setIndent(6)

        self.verticalLayout.addWidget(self.nRowLabel, 0, Qt.AlignLeft)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setSizeConstraint(QLayout.SetFixedSize)
        self.rowSlider = QSlider(headerForm)
        self.rowSlider.setObjectName(u"rowSlider")
        sizePolicy2.setHeightForWidth(self.rowSlider.sizePolicy().hasHeightForWidth())
        self.rowSlider.setSizePolicy(sizePolicy2)
        self.rowSlider.setMinimum(1)
        self.rowSlider.setMaximum(5)
        self.rowSlider.setPageStep(1)
        self.rowSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_3.addWidget(self.rowSlider)

        self.valueNRowSlider = QLabel(headerForm)
        self.valueNRowSlider.setObjectName(u"valueNRowSlider")
        sizePolicy2.setHeightForWidth(self.valueNRowSlider.sizePolicy().hasHeightForWidth())
        self.valueNRowSlider.setSizePolicy(sizePolicy2)

        self.horizontalLayout_3.addWidget(self.valueNRowSlider)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.cellActionsLabel = QLabel(headerForm)
        self.cellActionsLabel.setObjectName(u"cellActionsLabel")
        self.cellActionsLabel.setIndent(6)

        self.verticalLayout.addWidget(self.cellActionsLabel)

        self.joinButton = QPushButton(headerForm)
        self.joinButton.setObjectName(u"joinButton")
        self.joinButton.setFocusPolicy(Qt.NoFocus)

        self.verticalLayout.addWidget(self.joinButton)

        self.splitButton = QPushButton(headerForm)
        self.splitButton.setObjectName(u"splitButton")
        self.splitButton.setFocusPolicy(Qt.NoFocus)

        self.verticalLayout.addWidget(self.splitButton)

        self.emptyButton = QPushButton(headerForm)
        self.emptyButton.setObjectName(u"emptyButton")
        self.emptyButton.setFocusPolicy(Qt.NoFocus)

        self.verticalLayout.addWidget(self.emptyButton)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.alignLabel = QLabel(headerForm)
        self.alignLabel.setObjectName(u"alignLabel")
        self.alignLabel.setIndent(6)

        self.verticalLayout.addWidget(self.alignLabel, 0, Qt.AlignLeft)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.alignLeftButton = QPushButton(headerForm)
        self.alignLeftButton.setObjectName(u"alignLeftButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.alignLeftButton.sizePolicy().hasHeightForWidth())
        self.alignLeftButton.setSizePolicy(sizePolicy3)
        self.alignLeftButton.setFocusPolicy(Qt.NoFocus)
        self.alignLeftButton.setText(u"<")
        self.alignLeftButton.setCheckable(False)
        self.alignLeftButton.setFlat(False)

        self.horizontalLayout_5.addWidget(self.alignLeftButton)

        self.alignCenterButton = QPushButton(headerForm)
        self.alignCenterButton.setObjectName(u"alignCenterButton")
        sizePolicy3.setHeightForWidth(self.alignCenterButton.sizePolicy().hasHeightForWidth())
        self.alignCenterButton.setSizePolicy(sizePolicy3)
        self.alignCenterButton.setFocusPolicy(Qt.NoFocus)
        self.alignCenterButton.setText(u"|")

        self.horizontalLayout_5.addWidget(self.alignCenterButton)

        self.alignRightButton = QPushButton(headerForm)
        self.alignRightButton.setObjectName(u"alignRightButton")
        sizePolicy3.setHeightForWidth(self.alignRightButton.sizePolicy().hasHeightForWidth())
        self.alignRightButton.setSizePolicy(sizePolicy3)
        self.alignRightButton.setFocusPolicy(Qt.NoFocus)
        self.alignRightButton.setText(u">")

        self.horizontalLayout_5.addWidget(self.alignRightButton)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.acceptButton = QPushButton(headerForm)
        self.acceptButton.setObjectName(u"acceptButton")
        self.acceptButton.setFocusPolicy(Qt.NoFocus)

        self.verticalLayout.addWidget(self.acceptButton)

        self.cancelButton = QPushButton(headerForm)
        self.cancelButton.setObjectName(u"cancelButton")
        self.cancelButton.setFocusPolicy(Qt.NoFocus)

        self.verticalLayout.addWidget(self.cancelButton)


        self.horizontalLayout_4.addLayout(self.verticalLayout)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(headerForm)
        self.label.setObjectName(u"label")
        self.label.setIndent(6)

        self.verticalLayout_3.addWidget(self.label)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.textButton = QPushButton(headerForm)
        self.textButton.setObjectName(u"textButton")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.textButton.sizePolicy().hasHeightForWidth())
        self.textButton.setSizePolicy(sizePolicy4)
        self.textButton.setMinimumSize(QSize(100, 30))
        self.textButton.setBaseSize(QSize(100, 0))
        self.textButton.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_6.addWidget(self.textButton)

        self.imageButton = QPushButton(headerForm)
        self.imageButton.setObjectName(u"imageButton")
        sizePolicy4.setHeightForWidth(self.imageButton.sizePolicy().hasHeightForWidth())
        self.imageButton.setSizePolicy(sizePolicy4)
        self.imageButton.setMinimumSize(QSize(100, 30))
        self.imageButton.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_6.addWidget(self.imageButton)

        self.studentNameButton = QPushButton(headerForm)
        self.studentNameButton.setObjectName(u"studentNameButton")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.studentNameButton.sizePolicy().hasHeightForWidth())
        self.studentNameButton.setSizePolicy(sizePolicy5)
        self.studentNameButton.setMinimumSize(QSize(0, 30))
        self.studentNameButton.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_6.addWidget(self.studentNameButton)

        self.groupButton = QPushButton(headerForm)
        self.groupButton.setObjectName(u"groupButton")
        sizePolicy5.setHeightForWidth(self.groupButton.sizePolicy().hasHeightForWidth())
        self.groupButton.setSizePolicy(sizePolicy5)
        self.groupButton.setMinimumSize(QSize(0, 30))
        self.groupButton.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_6.addWidget(self.groupButton)

        self.dateButton = QPushButton(headerForm)
        self.dateButton.setObjectName(u"dateButton")
        sizePolicy5.setHeightForWidth(self.dateButton.sizePolicy().hasHeightForWidth())
        self.dateButton.setSizePolicy(sizePolicy5)
        self.dateButton.setMinimumSize(QSize(0, 30))
        self.dateButton.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_6.addWidget(self.dateButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_6)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)


        self.retranslateUi(headerForm)

        QMetaObject.connectSlotsByName(headerForm)
    # setupUi

    def retranslateUi(self, headerForm):
        self.iconInfoLabel.setText("")
        self.infoLabel.setText("")
        self.nColumnLabel.setText(_(u"Columns"))
        self.valueNColumnSlider.setText("")
        self.nRowLabel.setText(_(u"Rows"))
        self.valueNRowSlider.setText("")
        self.cellActionsLabel.setText(_(u"Cell actions"))
#if QT_CONFIG(tooltip)
        self.joinButton.setToolTip(_(u"Join cells"))
#endif // QT_CONFIG(tooltip)
        self.joinButton.setText(_(u"Join"))
#if QT_CONFIG(tooltip)
        self.splitButton.setToolTip(_(u"Split cell"))
#endif // QT_CONFIG(tooltip)
        self.splitButton.setText(_(u"Split"))
#if QT_CONFIG(tooltip)
        self.emptyButton.setToolTip(_(u"Empty cell"))
#endif // QT_CONFIG(tooltip)
        self.emptyButton.setText(_(u"Empty"))
        self.alignLabel.setText(_(u"Align"))
#if QT_CONFIG(tooltip)
        self.alignLeftButton.setToolTip(_(u"Align left"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.alignCenterButton.setToolTip(_(u"Align center"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.alignRightButton.setToolTip(_(u"Align right"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.acceptButton.setToolTip(_(u"Accept changes"))
#endif // QT_CONFIG(tooltip)
        self.acceptButton.setText(_(u"Accept"))
#if QT_CONFIG(tooltip)
        self.cancelButton.setToolTip(_(u"Cancel changes"))
#endif // QT_CONFIG(tooltip)
        self.cancelButton.setText(_(u"Cancel"))
        self.label.setText(_(u"Insert actions"))
#if QT_CONFIG(tooltip)
        self.textButton.setToolTip(_(u"Insert text"))
#endif // QT_CONFIG(tooltip)
        self.textButton.setText(_(u"Text"))
#if QT_CONFIG(tooltip)
        self.imageButton.setToolTip(_(u"Insert image"))
#endif // QT_CONFIG(tooltip)
        self.imageButton.setText(_(u"Image"))
#if QT_CONFIG(tooltip)
        self.studentNameButton.setToolTip(_(u"Insert student name field"))
#endif // QT_CONFIG(tooltip)
        self.studentNameButton.setText(_(u"Student name"))
#if QT_CONFIG(tooltip)
        self.groupButton.setToolTip(_(u"Insert group field"))
#endif // QT_CONFIG(tooltip)
        self.groupButton.setText(_(u"Group"))
#if QT_CONFIG(tooltip)
        self.dateButton.setToolTip(_(u"Insert date field"))
#endif // QT_CONFIG(tooltip)
        self.dateButton.setText(_(u"Date"))
    # retranslateUi


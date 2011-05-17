# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement, absolute_import

import sys
import numpy
import cPickle as pickle

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QPoint, QString
from PyQt4.QtGui import QGraphicsScene, QGraphicsRectItem, QFileDialog

from itertools import imap

from .level_editor_mainwindow import Ui_MainWindow
from .levelpart import LevelPart

import levelformat

class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.level = QGraphicsScene(self.ui.graphicsView)
        self.ui.graphicsView.setScene(self.level)

        self.ui.action_New.triggered.connect(self.onNew)

        self.ui.actionNew_Rect.triggered.connect(self.onNewRect)

        self.file_save = QFileDialog(self, 'Choose file', '.')
        self.file_save.setAcceptMode(QFileDialog.AcceptSave)
        self.file_save.setFileMode(QFileDialog.AnyFile)
        self.file_save.fileSelected.connect(self.onSave)
        self.ui.action_Save.triggered.connect(self.file_save.show)

        self.file_open = QFileDialog(self, 'Choose level to open', '.')
        self.file_open.setAcceptMode(QFileDialog.AcceptOpen)
        self.file_open.setFileMode(QFileDialog.AnyFile)
        self.file_open.fileSelected.connect(self.onOpen)
        self.ui.action_Open.triggered.connect(self.file_open.show)

        self.dirty = False
        self.level.changed.connect(lambda: self.__setattr__('dirty', True))

    def onNewRect(self):
        rect = LevelPart(-30, -10, 60, 20)
        self.level.addItem(rect)

    def onNew(self):
        if self.dirty:
            self.file_save.show()

        self.level.clear()

    def onOpen(self, filename):
        if self.dirty:
            self.file_save.show()
        with open(filename) as levelfile:
            self.level.clear()
            data = pickle.load(levelfile)
            if data.version > 1:
                print('Too high version:', data.version)
                return
            for rect in data.rects:
                part = LevelPart(rect.x, rect.y, rect.w, rect.h)
                part.translate(rect.dx, rect.dy)
                self.level.addItem(part)

    def onSave(self, filename=None):
        rects = []
        for item in self.ui.graphicsView.items():
            itemrect = item.rect()
            itemlocation = item.scenePos()
            rects.append(levelformat.LevelRect(itemrect.x(), itemrect.y(),
                                   itemrect.width(), itemrect.height(),
                                   itemlocation.x(), itemlocation.y()))

        with open(filename, 'wb') as levelfile:
            pickle.dump(levelformat.LevelDescriptor(1, rects), levelfile, protocol=2)

def leveleditor_main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())

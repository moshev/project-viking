# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement, absolute_import

import sys
import numpy
import cPickle as pickle

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QPoint, QString, pyqtSlot
from PyQt4.QtGui import QGraphicsScene, QGraphicsRectItem, QFileDialog

from itertools import imap
from util import iapply

from .level_editor_mainwindow import Ui_MainWindow
from .levelpart import LevelPart
from .scalehandle import ScaleHandle

import levelformat

__all__ = ['Main', 'leveleditor_main']

class Main(QtGui.QMainWindow):
    def __init__(self):
        super(Main, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.level = self.ui.graphicsView.scene() or QGraphicsScene()
        self.ui.graphicsView.setScene(self.level)
        self.level.selectionChanged.connect(self.onSelectionChanged)

        self.ui.action_New.triggered.connect(self.onNew)

        self.ui.actionNew_Rect.triggered.connect(self.onNewRect)
        self.ui.actionDelete_Rects.triggered.connect(self.onDeleteRects)

        self.file_save = QFileDialog(self, 'Choose file to save as', '.')
        self.file_save.setAcceptMode(QFileDialog.AcceptSave)
        self.file_save.setFileMode(QFileDialog.AnyFile)
        self.file_save.setDefaultSuffix('level')
        self.file_save.setNameFilter('.level files (*.level)')
        self.file_save.fileSelected.connect(self.onSave)
        self.file_save.setModal(True)
        self.ui.action_Save.triggered.connect(self.file_save.show)

        self.file_open = QFileDialog(self, 'Choose level to open', '.')
        self.file_open.setAcceptMode(QFileDialog.AcceptOpen)
        self.file_open.setFileMode(QFileDialog.ExistingFile)
        self.file_open.setNameFilter('.level files (*.level)')
        self.file_open.fileSelected.connect(self.onOpen)
        self.file_open.setModal(True)
        self.ui.action_Open.triggered.connect(self.file_open.show)
        self.handles = []
        self.original_selection_rect = QtCore.QRectF()
        self.selection_rect = QtCore.QRectF()


    def _addrect(self, x, y, w, h, cx=0, cy=0):
        rect = LevelPart(x, y, w, h)
        rect.partMoved.connect(self.onRectMoved)
        rect.setPos(cx, cy)
        self.level.addItem(rect)


    @pyqtSlot(float, float, float, float)
    def onSelectionRectChanged(self, dleft, dtop, dright, dbottom):
        pass


    @pyqtSlot()
    def onSelectionChanged(self):
        if self.level is None:
            return

        # remove selector handles
        iapply(self.level.removeItem, self.handles)
        del self.handles[:]

        selection = self.level.selectedItems()
        if len(selection) > 0:
            boundingRect = QtCore.QRectF()
            for rect in imap(lambda i: i.boundingRect().translated(i.pos()), selection):
                boundingRect |= rect
            left = boundingRect.left()
            right = boundingRect.right()
            top = boundingRect.top()
            bottom = boundingRect.bottom()
            cx = (left + right) / 2
            cy = (top + bottom) / 2
            self.handles[:] = [ScaleHandle(left, top, xmap=0, ymap=0),
                               ScaleHandle(cx, top, ymap=0),
                               ScaleHandle(right, top, xmap=1, ymap=0),
                               ScaleHandle(right, cy, xmap=1),
                               ScaleHandle(right, bottom, xmap=1, ymap=1),
                               ScaleHandle(cx, bottom, ymap=1),
                               ScaleHandle(left, bottom, xmap=0, ymap=1),
                               ScaleHandle(left, cy, xmap=0),]

            iapply(self.level.addItem, self.handles)

            # hook up signals. Each handle moves each handle and reports change to the level editor
            for h1 in self.handles:
                h1.selectionRectChanged.connect(self.onSelectionRectChanged)
                for h2 in self.handles:
                    if h1 != h2:
                        h1.selectionRectChanged.connect(h2.onSelectionRectChanged)


    @pyqtSlot(QtGui.QGraphicsObject, QtCore.QPointF)
    def onRectMoved(self, rect, dist):
        if rect.isSelected():
            for h in self.handles:
                h.moveBy(dist.x(), dist.y())


    @pyqtSlot()
    def onNewRect(self):
        self._addrect(-32, -16, 64, 32)


    @pyqtSlot()
    def onDeleteRects(self):
        for item in self.level.selectedItems():
            self.level.removeItem(item)


    @pyqtSlot()
    def onNew(self):
        self.level.clear()


    @pyqtSlot(str)
    def onOpen(self, filename):
        with open(filename) as levelfile:
            self.level.clear()
            data = pickle.load(levelfile)
            if data.version > 1:
                print('Too high version:', data.version)
                return
            for rect in data.rects:
                self._addrect(rect.x, rect.y, rect.w, rect.h, rect.dx, rect.dy)


    @pyqtSlot(str)
    def onSave(self, filename=None):
        rects = []
        for item in self.ui.graphicsView.items():
            if isinstance(item, LevelPart):
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


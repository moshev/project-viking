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


def itemrects(items):
    '''generator of tuples (item, itemrect) for each item in items that has a rect'''
    return ((item, item.data(0).toRectF())
            for item in items
            if not item.data(0).isNull())


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
        self.selected_rect_item = QtGui.QGraphicsRectItem()


    def _addrect(self, x, y, w, h, cx=0, cy=0):
        rect = LevelPart(x, y, w, h)
        rect.partMoved.connect(self.onRectMoved)
        rect.setPos(cx, cy)
        self.level.addItem(rect)


    @pyqtSlot(float, float, float, float)
    def onSelectionRectChanged(self):
        self.selected_rect_item.setRect(self.selection_rect)
        sx = self.selection_rect.width() / self.original_selection_rect.width()
        sy = self.selection_rect.height() / self.original_selection_rect.height()
        for item, rect in itemrects(self.level.selectedItems()):
            orect = item.data(1)
            if orect.isNull():
                orect = QtCore.QRectF(rect)
                item.setData(1, orect)
            else:
                orect = orect.toRectF()
            rect.setWidth(orect.width() * sx)
            rect.setHeight(orect.height() * sy)
            item.setData(0, rect)

    @pyqtSlot()
    def onSelectionChanged(self):
        if self.level is None:
            return

        if self.selected_rect_item.scene() == self.level:
            self.level.removeItem(self.selected_rect_item)

        # remove selector handles
        iapply(self.level.removeItem, self.handles)
        del self.handles[:]

        selection = self.level.selectedItems()
        if len(selection) > 0:
            boundingRect = QtCore.QRectF()
            for item, rect in itemrects(selection):
                item.setData(1, rect)
                boundingRect |= rect.translated(item.pos())
            self.selection_rect = boundingRect
            self.original_selection_rect = QtCore.QRectF(boundingRect)
            self.selected_rect_item = QtGui.QGraphicsRectItem(boundingRect)
            self.level.addItem(self.selected_rect_item)
            self.handles[:] = [ScaleHandle(boundingRect, 0, 0),
                               ScaleHandle(boundingRect, 0.5, 0),
                               ScaleHandle(boundingRect, 1, 0),
                               ScaleHandle(boundingRect, 1, 0.5),
                               ScaleHandle(boundingRect, 1, 1),
                               ScaleHandle(boundingRect, 0.5, 1),
                               ScaleHandle(boundingRect, 0, 1),
                               ScaleHandle(boundingRect, 0, 0.5),]

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
            self.selection_rect.translate(dist)
            self.onSelectionRectChanged()
            for h in self.handles:
                h.onSelectionRectChanged()


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
        for item, rect in itemrects(self.level.items()):
            pos = item.scenePos()
            rects.append(levelformat.LevelRect(rect.x(), rect.y(),
                                               rect.width(), rect.height(),
                                               pos.x(), pos.y()))

        with open(filename, 'wb') as levelfile:
            pickle.dump(levelformat.LevelDescriptor(1, rects), levelfile, protocol=2)


def leveleditor_main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())


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


def parts(items):
    '''generator of tuples (item, itemrect) for each item in items that has a rect'''
    return (part
            for part in (item.data(0).toPyObject()
                         for item in items)
            if isinstance(part, LevelPart))


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
        self.level.addItem(rect)


    @pyqtSlot()
    def onSelectionRectChanged(self):
        self.selected_rect_item.setRect(self.selection_rect)
        srw = self.selection_rect.width()
        srh = self.selection_rect.height()
        srtl = self.selection_rect.topLeft()
        for part in parts(self.level.selectedItems()):
            relrect = part.data(1).toRectF()
            part.setWidth(relrect.width() * srw)
            part.setHeight(relrect.height() * srh)
            newpos = QtCore.QPointF(srw * relrect.left(), srh * relrect.top()) + srtl
            part.setPos(newpos)

    @pyqtSlot()
    def onSelectionChanged(self):
        if self.level is None:
            return

        if self.selected_rect_item.scene() == self.level:
            self.level.removeItem(self.selected_rect_item)

        # remove selector handles
        iapply(self.level.removeItem, self.handles)
        del self.handles[:]

        selection = list(parts(self.level.selectedItems()))
        if len(selection) > 0:
            boundingRect = QtCore.QRectF()
            for part in selection:
                boundingRect |= part.boundingRect().translated(part.pos())
            self.selection_rect = boundingRect
            srw = boundingRect.width()
            srh = boundingRect.height()
            srtl = boundingRect.topLeft()
            for part in selection:
                pos = part.pos() - srtl
                sz = part.size()
                relrect = QtCore.QRectF(pos.x() / srw, pos.y() / srh,
                                        sz.width() / srw, sz.height() / srh)
                part.setData(1, relrect)

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
                self._addrect(rect.x + rect.dx, rect.y + rect.dy, rect.w, rect.h)


    @pyqtSlot(str)
    def onSave(self, filename=None):
        rects = []
        for part in parts(self.level.items()):
            pos = part.pos()
            # 0, 0 because legacy format ;_;
            rects.append(levelformat.LevelRect(pos.x(), pos.y(),
                                               part.width(), part.height(),
                                               0, 0))

        with open(filename, 'wb') as levelfile:
            pickle.dump(levelformat.LevelDescriptor(1, rects), levelfile, protocol=2)


def leveleditor_main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())


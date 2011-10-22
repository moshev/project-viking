# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsObject, QColor

class ScaleHandle(QGraphicsObject):
    '''A handle that scales a selection of items'''


    def __init__(self, x, y, r=6, xmap=None, ymap=None, parent=None):
        '''
        xmap/ymap define which part of the rect this handle controls

        xmap: 0 - left
              1 - right
              None - neither

        ymap: 0 - top
              1 - bottom
              None - neither
        '''
        super(ScaleHandle, self).__init__(parent)
        self.rect = QtCore.QRectF(x - r, y - r, r * 2, r * 2)
        self.setFlags(QGraphicsItem.ItemIsMovable)
        self.xmap = xmap
        self.ymap = ymap


    def boundingRect(self):
        return self.rect


    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.black)
        painter.setBrush(QBrush(QColor(144,51,77)))
        painter.drawEllipse(self.rect)


    # emitted when this handle is moved. args: dleft, dtop, dbottom, dright
    selectionRectChanged = pyqtSignal(float, float, float, float)


    @pyqtSlot(float, float, float, float)
    def onSelectionRectChanged(self, dleft, dtop, dright, dbottom):
        '''Handle a change in the selection rect from other handles'''
        dx, dy = self.dxyFromDltbr(dleft, dtop, dright, dbottom)
        self.moveBy(dx, dy)


    def dxyFromDltbr(self, *dltbr):
        '''dxyFromDltbr(self, dleft, dtop, dright, dbottom)
        Returns a tuple (dx, dy) by which to move this handle,
        where dx or dy might be set to 0 to account for restrictions in movement.
        '''
        dx = dy = 0.0
        if self.xmap is not None:
            dx = dltbr[2 * self.xmap]

        if self.ymap is not None:
            dy = dltbr[2 * self.ymap + 1]

        return (dx, dy)


    def dltbrFromDxy(self, dx, dy):
        '''dltbrFromDxy(self, dx, dy)
        Returns a 4-tuple (dleft, dtop, dright, dbottom) describing
        the change in the selection rect.
        '''
        delta = [0.0] * 4
        if self.xmap is not None:
            delta[self.xmap * 2] = dx
        if self.ymap is not None:
            delta[self.ymap * 2 + 1] = dy
        return tuple(delta)


    def mouseMoveEvent(self, event):
        moved = event.pos() - event.lastPos()
        dx, dy = 0.0, 0.0
        if self.xmap is not None:
            dx = moved.x()
        if self.ymap is not None:
            dy = moved.y()

        self.moveBy(dx, dy)
        dltbr = self.dltbrFromDxy(dx, dy)
        self.selectionRectChanged.emit(*dltbr)



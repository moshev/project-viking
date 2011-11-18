# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsObject, QColor

class ScaleHandle(QGraphicsObject):
    '''A handle that scales a selection of items'''


    def __init__(self, selection_rect, x, y, r=6, parent=None):
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
        self.x = x
        self.y = y
        self.r = r
        self.selection_rect = selection_rect
        self.setPos(*self._pos)


    @property
    def _pos(self):
        tl = self.selection_rect.topLeft()
        w = self.selection_rect.width()
        h = self.selection_rect.height()
        cx = tl.x() + self.x * w
        cy = tl.y() + self.y * h
        return (cx, cy)


    @property
    def xmap(self):
        '''Which side of the rectangle this handle controls horizontally
        0 - left; 1 - right; None - neither'''
        xmap = int(self.x)
        if xmap == self.x:
            return xmap
        else:
            return None


    @property
    def ymap(self):
        '''Which side of the rectangle this handle controls vertically
        0 - top; 1 - bottom; None - neither'''
        ymap = int(self.y)
        if ymap == self.y:
            return ymap
        else:
            return None


    def boundingRect(self):
        r = self.r
        return QtCore.QRectF(-r - 2, -r - 2, r * 2 + 4, r * 2 + 4)


    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.black)
        painter.setBrush(QBrush(QColor(144,51,77)))
        painter.drawEllipse(self.boundingRect())


    # emitted when this handle is moved, after the selection rect has been changed.
    selectionRectChanged = pyqtSignal()


    @pyqtSlot()
    def onSelectionRectChanged(self):
        self.setPos(*self._pos)


    def dxyFromDltrb(self, *dltrb):
        '''dxyFromDltrb(self, dleft, dtop, dright, dbottom)
        Returns a tuple (dx, dy) by which to move this handle,
        where dx or dy might be set to 0 to account for restrictions in movement.
        '''
        dx = dy = 0.0
        if self.xmap is not None:
            dx = dltrb[2 * self.xmap]

        if self.ymap is not None:
            dy = dltrb[2 * self.ymap + 1]

        return (dx, dy)


    def dltrbFromDxy(self, dx, dy):
        '''dltrbFromDxy(self, dx, dy)
        Returns a 4-tuple (dleft, dtop, dright, dbottom) describing
        the change in the selection rect.
        '''
        delta = [0.0] * 4
        if self.xmap is not None:
            delta[self.xmap * 2] = dx
        if self.ymap is not None:
            delta[self.ymap * 2 + 1] = dy
        return tuple(delta)


    def mousePressEvent(self, event):
        event.accept()


    def mouseMoveEvent(self, event):
        moved = event.pos() - event.lastPos()
        dx, dy = 0.0, 0.0
        if self.xmap is not None:
            dx = moved.x()
        if self.ymap is not None:
            dy = moved.y()

        dltrb = self.dltrbFromDxy(dx, dy)
        self.selection_rect.adjust(*dltrb)
        self.selectionRectChanged.emit()
        self.setPos(*self._pos)



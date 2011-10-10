# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsObject, QColor

class ScaleHandle(QGraphicsObject):
    '''A handle that scales a selection of items'''
    def __init__(self, x, y, r=6, restrictx=False, restricty=False, parent=None):
        super(ScaleHandle, self).__init__(parent)
        self.rect = QtCore.QRectF(x - r, y - r, r * 2, r * 2)
        self.setFlags(QGraphicsItem.ItemIsMovable)
        self.restrictx = restrictx
        self.restricty = restricty


    def boundingRect(self):
        return self.rect


    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.black)
        painter.setBrush(QBrush(QColor(144,51,77)))
        painter.drawEllipse(self.rect)


    def mouseMoveEvent(self, event):
        moved = event.pos() - event.lastPos()
        if self.restrictx:
            moved.setX(0)
        if self.restricty:
            moved.setY(0)
        self.moveBy(moved.x(), moved.y())
        self.handleMoved.emit(moved)


    handleMoved = pyqtSignal(QtCore.QPointF)




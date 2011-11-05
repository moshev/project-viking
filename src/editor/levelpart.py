# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsObject

class LevelPart(QGraphicsObject):
    '''A part of a level - just a rectangle.'''

    # [(regular pen, brush), (selected pen, brush)]
    STYLE = [(Qt.black, QBrush(Qt.blue, Qt.SolidPattern)),
             (Qt.red, QBrush(Qt.red, Qt.Dense4Pattern))]

    def __init__(self, x, y, w, h, scene=None):
        '''Create a level part occupying the given rectangle.'''

        super(LevelPart, self).__init__(scene)
        rect = QtCore.QRectF(x, y, w, h)
        self.setData(0, rect)
        self.setFlags(self.flags() | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIsSelectable)


    @property
    def rect(self):
        return self.data(0).toRectF()


    def paint(self, painter, option, widget):
        pen, brush = LevelPart.STYLE[self.isSelected()]
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(self.rect)


    def boundingRect(self):
        return self.rect


    def mouseMoveEvent(self, event):
        moved = event.pos() - event.lastPos()
        super(LevelPart, self).mouseMoveEvent(event)
        self.partMoved.emit(self, moved)


    partMoved = pyqtSignal(QGraphicsObject, QtCore.QPointF)


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
        self._size = QtCore.QSizeF(w, h)
        self.setPos(x, y)
        # dirty hack since list of selected items erases the proper class wtf???
        self.setData(0, self)
        self.setFlags(self.flags() | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIsSelectable)


    def size(self):
        '''Returns a QPointF with this part's size'''
        return self._size


    def width(self):
        return self._size.width()


    def setWidth(self, w):
        self._size.setWidth(w)


    def height(self):
        return self._size.height()


    def setHeight(self, h):
        self._size.setHeight(h)


    def paint(self, painter, option, widget):
        pen, brush = LevelPart.STYLE[self.isSelected()]
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(self.boundingRect())


    def boundingRect(self):
        return QtCore.QRectF(0, 0, self._size.width(), self._size.height())


    def mouseMoveEvent(self, event):
        moved = event.pos() - event.lastPos()
        super(LevelPart, self).mouseMoveEvent(event)
        self.partMoved.emit(self, moved)


    partMoved = pyqtSignal(QGraphicsObject, QtCore.QPointF)


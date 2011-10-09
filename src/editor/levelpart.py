# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsRectItem

class LevelPart(QGraphicsRectItem):
    '''A part of a level - just a rectangle.'''

    # [(regular pen, brush), (selected pen, brush)]
    STYLE = [(Qt.black, QBrush(Qt.blue, Qt.SolidPattern)),
             (Qt.red, QBrush(Qt.red, Qt.Dense4Pattern))]

    def __init__(self, x, y, w, h, onMove=None, scene=None):
        '''Create a level part occupying the given rectangle and with the given styles.
        onMove is called as onMove(self, dist)
        style_chooser - a callable that takes a boolean value (selected)
                        and returns a tuple (pen, brush)'''

        super(LevelPart, self).__init__(x, y, w, h, scene=scene)
        self.setFlags(self.flags() | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIsSelectable)
        self.onMove = onMove
        if callable(onMove):
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)


    def itemChange(self, change, variant):
        if change == QGraphicsItem.ItemPositionHasChanged:
            newpos = variant.toPointF()
            self.onMove(self, self.pos() - newpos)
        return super(QGraphicsRectItem, self).itemChange(change, variant)


    def paint(self, painter, option, widget):
        pen, brush = LevelPart.STYLE[self.isSelected()]
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(self.rect())


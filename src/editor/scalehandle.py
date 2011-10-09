# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsEllipseItem

class ScaleHandle(QGraphicsEllipseItem):
    '''A handle that scales a selection of items'''
    def __init__(self, x, y, r=4, parent=None):
        super(ScaleHandle, self).__init__(x - r, y - r, r * 2, r * 2, parent)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)


    def itemChange(self, change, variant):
        if change == QGraphicsItem.ItemPositionChange:
            newpos = variant.toPointF()
            pos = self.pos()
            return QtCore.QVariant(QtCore.QPointF(pos.x(), newpos.y()))
        else:
            return super(ScaleHandle, self).itemChange(change, variant)


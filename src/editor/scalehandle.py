# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPainter, QPen, QBrush, QGraphicsItem, QGraphicsEllipseItem

class ScaleHandle(QGraphicsEllipseItem):
    '''A handle that scales a selection of items'''
    def __init__(self, x, y, r=8, parent=None):
        super(ScaleHandle, self).__init__(x - r, y - r, r * 2, r * 2, parent)


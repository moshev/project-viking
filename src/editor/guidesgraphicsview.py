# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

import os
import math
from PyQt4 import QtCore, QtGui

__all__ = ['GuidesGraphicsView']

class GuidesGraphicsView(QtGui.QGraphicsView):
    '''A QGraphicsView which also draws guides to indicate where the coordinate system is.'''

    def __init__(self, *args):
        super(GuidesGraphicsView, self).__init__(*args)
        self.spacing = 64
        self.grid_pen = QtGui.QPen(QtCore.Qt.black)
        self.grid_pen.setStyle(QtCore.Qt.DotLine)
        self.axes_pen = QtGui.QPen(QtCore.Qt.darkGreen)


    def drawBackground(self, painter, rect):
        '''Draw the background coordinate system'''

        p1 = QtCore.QPointF()
        p2 = QtCore.QPointF()
        p1.setX(rect.left())
        p2.setX(rect.right())
        painter.setPen(self.grid_pen)
        left_grid, right_grid, top_grid, bottom_grid = map(lambda x: int(x) - int(x) % self.spacing,
                                                           (rect.left(), rect.right() + self.spacing,
                                                            rect.top(), rect.bottom() + self.spacing))

        for y in range(top_grid, bottom_grid, self.spacing):
            p1.setY(y)
            p2.setY(y)
            if y == 0:
                painter.setPen(self.axes_pen)
            painter.drawLine(p1, p2)
            if y == 0:
                # restore pen
                painter.setPen(self.grid_pen)

        p1.setY(rect.top())
        p2.setY(rect.bottom())
        for x in range(left_grid, right_grid, self.spacing):
            p1.setX(x)
            p2.setX(x)
            if x == 0:
                painter.setPen(self.axes_pen)
            painter.drawLine(p1, p2)
            if x == 0:
                # restore pen
                painter.setPen(self.grid_pen)


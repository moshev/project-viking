# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

import os
import numpy
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSlot, QPoint, QRect, Qt
from PyQt4.QtGui import QPainter, QPen, QBrush
try:
    import cPickle as pickle
except ImportError:
    import pickle
from components import hitbox

class HitboxEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(HitboxEditorWidget, self).__init__(parent)
        self.hbp_pen = Qt.gray
        self.hba_pen = Qt.red
        self.hbp_brush = QBrush(Qt.gray, Qt.CrossPattern)
        self.hba_brush = QBrush(Qt.red, Qt.DiagCrossPattern)
        self.coords_pen = QtGui.QColor(Qt.green).light()
        self.load("untitled.png")

    def sizeHint(self):
        return QtCore.QSize(600, 600)

    def minimumSizeHint(self):
        return QtCore.QSize(100, 200)

    @pyqtSlot()
    def save(self):
        points = {'sp': numpy.array((self.sp.x(), self.sp.y())),
                  'hba': hitbox((self.hba.x(), self.hba.y()),
                                (self.hba.width(), self.hba.height())),
                  'hbp': hitbox((self.hbp.x(), self.hbp.y()),
                                (self.hbp.width(), self.hbp.height()))}

        with file(self.points_file, 'wb') as data:
            pickle.dump(points, data, 2)
            self.dirty = False

    @pyqtSlot(str)
    def load(self, imagefile):
        imagefile = str(imagefile)
        self.image_file = imagefile
        if os.path.exists(self.image_file):
            self.image = QtGui.QImage(self.image_file)
        else:
            self.image = None

        self.points_file = os.path.splitext(imagefile)[0] + '.points'
        if os.path.exists(self.points_file):
            with file(self.points_file, 'rb') as data:
                points = pickle.load(data)
                self.sp = QPoint(points['sp'][0], points['sp'][1])
                self.hba = QRect(points['hba'].point[0], points['hba'].point[1],
                                 points['hba'].size[0], points['hba'].size[1])
                self.hbp = QRect(points['hbp'].point[0], points['hbp'].point[1],
                                 points['hbp'].size[0], points['hbp'].size[1])
        else:
            self.sp = QPoint(0, 0)
            self.hba = QRect(0, 0, 20, 20)
            self.hbp = QRect(0, 0, 40, 40)

        self.dirty = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.black)

        painter.setPen(self.coords_pen)
        painter.drawLine(0, self.height () // 2, self.width(), self.height() // 2)
        painter.drawLine(self.width() // 2, 0, self.width() // 2, self.height())

        painter.translate(self.width() // 2, self.height() // 2)
        if (self.image):
            painter.drawImage(self.sp, self.image)

            painter.setPen(self.hbp_pen)
            painter.setBrush(self.hbp_brush)
            painter.drawRect(self.hbp)

            painter.setPen(self.hba_pen)
            painter.setBrush(self.hba_brush)
            painter.drawRect(self.hba)

        painter.setPen(Qt.white)
        painter.drawText(QPoint(0, 20), self.points_file)
        painter.drawText(QPoint(0, 50), self.image_file)


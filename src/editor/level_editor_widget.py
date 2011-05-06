# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement


from PyQt4 import QtCore, QtGui

class LevelEditorWidget(QtGui.QGraphicsView):

    def on_NewRect(self):
        rect = QtGui.QGraphicsRectItem(-30, -10, 60, 20, scene=self.scene())

    def mousePressEvent(self, event):
        item = self.scene().itemAt(event.posF())
        if item is None:
            super(LevelEditorWidget, self).mousePressEvent(event)

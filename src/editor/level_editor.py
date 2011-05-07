# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QPoint, QString
from PyQt4.QtGui import QGraphicsScene, QGraphicsRectItem
from level_editor_mainwindow import Ui_MainWindow
from levelpart import LevelPart

class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.level = QGraphicsScene(self.ui.graphicsView)
        self.ui.graphicsView.setScene(self.level)
        
        self.ui.actionNew_Rect.triggered.connect(self.onNewRect)

    def onNewRect(self):
        rect = LevelPart(-30, -10, 60, 20)
        self.level.addItem(rect)


def leveleditor_main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())

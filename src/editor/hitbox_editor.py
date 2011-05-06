# -*- coding: utf-8 -*-

from __future__ import division, generators, print_function, with_statement
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QPoint, QString
from PyQt4.QtGui import QFileDialog, QAction, QApplication
from hitbox_editor_mainwindow import Ui_MainWindow

class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.action_Save.triggered.connect(self.ui.hitbox_editor.save)

        self.filechooser = QFileDialog(self, 'Choose frame', '.')
        self.filechooser.setAcceptMode(QFileDialog.AcceptOpen)
        self.filechooser.setFileMode(QFileDialog.AnyFile)
        self.filechooser.fileSelected.connect(self.ui.hitbox_editor.load)

        self.ui.action_Open.triggered.connect(self.filechooser.open)

        for dx, dy, key in [(1, 0, 'F'), (-1, 0, 'S'), (0, 1, 'D'), (0, -1, 'E')]:
            action = QAction(self)
            action.setObjectName('Move on ' + key)
            action.setShortcut(QApplication.translate("mainWindow", key, None, QApplication.UnicodeUTF8))
            action.triggered.connect(self.make_move_handler(QPoint(dx, dy)))
            self.addAction(action)

    def make_move_handler(self, delta):
        def handler():
            self.ui.hitbox_editor.sp += delta
            self.ui.hitbox_editor.update()
        return handler

def hitboxeditor_main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())

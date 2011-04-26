# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QFileDialog
from editor_main import Ui_mainWindow

class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        self.ui.action_Save.triggered.connect(self.ui.hitbox_editor.save)

        self.filechooser = QFileDialog(self, 'Choose frame', '.')
        self.filechooser.setAcceptMode(QFileDialog.AcceptOpen)
        self.filechooser.setFileMode(QFileDialog.AnyFile)
        self.filechooser.fileSelected.connect(self.ui.hitbox_editor.load)

        self.ui.action_Open.triggered.connect(self.filechooser.open)

def main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


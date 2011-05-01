# -*- coding: utf-8 -*-

from __future__ import division, generators, print_function, with_statement
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QPoint, QString
from PyQt4.QtGui import QFileDialog, QAction, QApplication
from editor_main import Ui_mainWindow

class Main(QtGui.QMainWindow):
    MODE_SPRITE = 0
    MODE_ACTIVE = 1
    MODE_PASSIVE = 2
    MODEKEY = {'Q': MODE_SPRITE,
               'A': MODE_ACTIVE,
               'P': MODE_PASSIVE}
    MODENAME = ['Sprite', 'Active hitbox', 'Passive hitbox']

    move = [(lambda hitbox_editor, delta: hitbox_editor.sp.__iadd__(QPoint(*delta))),
            (lambda hitbox_editor, delta: hitbox_editor.hba.translate(*delta)),
            (lambda hitbox_editor, delta: hitbox_editor.hbp.translate(*delta))]

    sizen = [(lambda hitbox_editor, delta: None),
             (lambda hitbox_editor, delta: hitbox_editor.hba.adjust(*delta)),
             (lambda hitbox_editor, delta: hitbox_editor.hbp.adjust(*delta))]

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

        self.mode = Main.MODE_SPRITE

        for key, mode in Main.MODEKEY.iteritems():
            action_mode = QAction(self)
            action_mode.setObjectName('Change mode for ' + key)
            action_mode.setShortcut(QApplication.translate('mainWindow', key, None, QApplication.UnicodeUTF8))
            action_mode.triggered.connect(self.make_mode_set(mode))
            self.addAction(action_mode)

        for idx, keys in [(0, 'FS'), (1, 'DE')]:
            for sign, key in zip((1, -1), keys):
                delta = [0, 0]
                delta[idx] = sign
                delta = tuple(delta)

                action_move = QAction(self)
                action_move.setObjectName('Move on ' + key)
                action_move.setShortcut(QApplication.translate('mainWindow', key, None, QApplication.UnicodeUTF8))
                action_move.triggered.connect(self.make_move_handler(delta))
                self.addAction(action_move)

        for idx, key in zip(xrange(4), 'JILK'):
            delta = [0, 0, 0, 0]

            # Largen
            # top and left get -1, width and height get +1
            delta[idx] = -1 if idx < 2 else 1

            action_sizen = QAction(self)
            action_sizen.setObjectName('Largen on ' + key)
            action_sizen.setShortcut(QApplication.translate('mainWindow', key, None,
                                                              QApplication.UnicodeUTF8))
            action_sizen.triggered.connect(self.make_size_handler(tuple(delta)))
            self.addAction(action_sizen)

            # Smallen
            # width and height get -1, top and left get +1
            delta[(idx + 2) % 4] = delta[idx]
            delta[idx] = 0
            key = 'Shift+' + key

            action_sizen = QAction(self)
            action_sizen.setObjectName('Smallen on ' + key)
            action_sizen.setShortcut(QApplication.translate('mainWindow', key, None,
                                                            QApplication.UnicodeUTF8))
            action_sizen.triggered.connect(self.make_size_handler(tuple(delta)))
            self.addAction(action_sizen)

    def make_mode_set(self, mode):
        '''Returns a function which sets mode to mode. Mode should be one of the MODE_
        constants above.'''

        def modeset():
            self.mode = mode

        return modeset

    def make_move_handler(self, delta):
        '''Returns a function which adjusts the location of the object for the
        current mode. Delta must be a tuple of two numbers'''

        def handler():
            Main.move[self.mode](self.ui.hitbox_editor, delta)
            self.ui.hitbox_editor.update()

        return handler

    def make_size_handler(self, delta):
        '''Returns a function which changes the size of the object for the
        current mode. Delta must be a tuple of 4 numbers for left, top, right, bottom'''

        def handler():
            Main.sizen[self.mode](self.ui.hitbox_editor, delta)
            self.ui.hitbox_editor.update()

        return handler

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value
        self.statusBar().showMessage('Mode: ' + Main.MODENAME[self._mode])

def main():
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    if len(sys.argv) > 1:
        window.ui.hitbox_editor.load(sys.argv[1])
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


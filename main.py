#!/usr/bin/python3
# -*- coding: utf-8 -*-  

import sys
import os
import json
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow
from canvas import RootCanvas

from serialpipe.serial import SConn
from serialpipe.keyboard import KeyboardPipe
from serialpipe.bgkeyboard import BGKeyboard


class WConfig():
    def __init__(self):
        with open("config.json", "r") as f:
            self.c = json.load(f)
        self.processConfig()

    def processConfig(self):
        c_canvas = self.c["canvas"]
        c_geometry = self.c["window"]["geometry"]
        c_canvas["width"] = c_geometry[2] - self.c["window"]["padding"] * 2
        c_canvas["height"] = c_geometry[3] - self.c["window"]["padding"] * 2
        c_canvas["cx"] = c_geometry[2] // 2
        c_canvas["cy"] = c_geometry[3] // 2
        c_canvas["corner_x"] = self.c["window"]["padding"]
        c_canvas["corner_y"] = self.c["window"]["padding"]


class RootWindow(QMainWindow):
    def __init__(self):
        self.rc = None
        self.kb = None
        self.app = QApplication(sys.argv)

        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # self.mainWindow = QMainWindow(self)
        # self.mainWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.setAutoFillBackground(True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, 100)
        self.setWindowTitle("SmartWHEEL")
        self.setWindowIcon(QIcon("logo.png"))
        self.setGeometry(*conf.c["window"]["geometry"])
        self.loadClasses()
        self.loadSerial()

        self.show()
        # self.qp = QPainter(self)

    def paintEvent(self, event):
        self.qp = QPainter(self)
        self.qp.setRenderHint(QPainter.Antialiasing)
        # self.qp.begin(self)
        self.draw()
        self.qp.end()

    def keyPressEvent(self, event):
        """
        Read keypresses from Qt and pass them to serialpipe
        """
        if self.kb is None:  # not initialized yet
            return

        self.kb.handleKeypress(event)

    def keyPressEventLegacy(self, event):
        """
        Old keypress event, dead code
        """
        if event.key() == QtCore.Qt.Key_W:
            conf.c["canvas"]["modules"][0]["class"].processKey(True)
        elif event.key() == QtCore.Qt.Key_A:
            conf.c["canvas"]["modules"][0]["class"].processKey(False)
        elif event.key() == QtCore.Qt.Key_Up:
            self.rc.ae.action("scrollUp")
        elif event.key() == QtCore.Qt.Key_Down:
            self.rc.ae.action("scrollDown")
        elif event.key() == QtCore.Qt.Key_Return:
            self.rc.ae.action("keyAction1")
        elif event.key() == QtCore.Qt.Key_Q:
            self.hide()
            QtCore.QTimer.singleShot(1000, self.show)  # Hide example
        elif event.key() == QtCore.Qt.Key_Escape:
            sys.exit(0)
        self.update()

    def loadSerial(self):
        """
        Init main serial connections
        """
        # TODO add serial.tools.miniterm in settings
        # TODO load them from loop
        try:
            self.sc = SConn("config/serial.json", self.rc.ae.callAction)
            self.sc.start()
        except BaseException as e:
            print(e)

        try:
            self.kb = KeyboardPipe("config/keyboard.json", self.rc.ae.callAction)
            self.kb.start()
        except BaseException as e:
            print(e)

        try:
            self.bkb = BGKeyboard("config/bgkeyboard.json", self.rc.ae.callAction)
            self.bkb.start()
        except BaseException as e:
            print(e)

    def loadClasses(self):
        self.rc = RootCanvas(conf.c["canvas"], self.update)

    def draw(self):
        self.rc.draw(self.qp)


def main():
    root = RootWindow()
    sys.exit(root.app.exec_())


if __name__ == "__main__":
    conf = WConfig()
    main()

#!/usr/bin/python3
# -*- coding: utf-8 -*-
import importlib
import sys
import os
import json
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow
from canvas import RootCanvas
import logging
from settings import SettingsWindow

# from serialpipe.serial import SConn
# from serialpipe.keyboard import KeyboardPipe
# from serialpipe.bgkeyboard import BGKeyboard


class WConfig:
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
        self.app = QApplication(sys.argv)
        super(RootWindow, self).__init__()
        self.rc = None
        self.kb = None
        logging.basicConfig(level=getattr(logging, conf.c["canvas"]["logging"].upper(), 2))
        self.logger = logging.getLogger(__name__)
        self.settings = SettingsWindow("settings_registry/config.json")
        self.settings.show()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # self.mainWindow = QMainWindow(self)
        # self.mainWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.setAutoFillBackground(True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
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
        if self.serialModules.get("serialpipe.keyboard") is None:  # not initialized yet
            return

        self.serialModules["serialpipe.keyboard"].handleKeypress(event)

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

        self.serialModules = {}

        for i in conf.c["canvas"]["serialModulesLoad"]:
            mod_name = conf.c["canvas"]["serialModules"][i]["name"]
            mod = importlib.import_module(mod_name)

            try:
                cls = mod.SConn(conf.c["canvas"]["serialModules"][i]["config"], self.rc.ae.callAction)
                cls.start()
                self.serialModules[mod_name] = cls
            except BaseException as e:
                self.logger.error("Failed to load " + mod_name + ": ", e)

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

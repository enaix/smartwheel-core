#!/usr/bin/python3
# -*- coding: utf-8 -*-
import importlib
import json
import logging
import math
import os
import sys
import weakref

import qdarktheme
from PyQt6 import QtCore
from PyQt6.QtCore import QEvent, QPoint, QSize, pyqtSlot
from PyQt6.QtGui import *
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QGraphicsBlurEffect,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from smartwheel import common, config, gui_tools
from smartwheel.canvas import RootCanvas
from smartwheel.settings import SettingsWindow


class WConfig(config.Config):
    def __init__(self, config_file, launch_config):
        super(WConfig, self).__init__(
            config_file, varsWhitelist=["modulesLoad", "serialModulesLoad"]
        )

        if not self.loadConfig():
            print("Fatal: error loading main config file. Exiting..")
            os._exit(1)

        self.launch_config = launch_config

        self.processConfig()

    def processConfig(self):
        self.c_canvas = config.Config(
            config_dict=self.c["canvas"],
            varsWhitelist=["modulesLoad", "serialModulesLoad"],
        )
        c_geometry = self.c["window"]["geometry"]
        self.c_canvas["width"] = c_geometry[2] - self.c["window"]["padding"] * 2
        self.c_canvas["height"] = c_geometry[3] - self.c["window"]["padding"] * 2
        self.c_canvas["cx"] = c_geometry[2] // 2
        self.c_canvas["cy"] = c_geometry[3] // 2
        self.c_canvas["corner_x"] = self.c["window"]["padding"]
        self.c_canvas["corner_y"] = self.c["window"]["padding"]


class RootWindow(QMainWindow):
    def __init__(self, conf):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(qdarktheme.load_stylesheet())
        super(RootWindow, self).__init__()
        self.conf = conf
        self.rc = None
        self.kb = None
        logging.basicConfig(
            level=getattr(logging, self.conf.c["canvas"]["logging"].upper(), 2)
        )
        self.logger = logging.getLogger(__name__)

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, True)
        # self.mainWindow = QMainWindow(self)
        # self.mainWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.dragPos = QtCore.QPoint()

        self.setAutoFillBackground(True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Smartwheel")
        self.setWindowIcon(QIcon("logo.png"))
        self.setGeometry(*self.conf.c["window"]["geometry"])
        self.loadClasses()
        self.loadSerial()
        self.initUI()

        self.postStart()

        self.settings = SettingsWindow(
            os.path.join(self.conf["basedir"], "settings_registry", "config.json"),
            os.path.join(
                self.conf["basedir"], "settings_registry", "config_defaults.json"
            ),
            weakref.ref(self),
            weakref.ref(self.conf),
            self.conf["basedir"],
        )
        # self.settings.show()

        self.appPostStart()

        self.show()
        # self.qp = QPainter(self)

    def appPostStart(self):
        common.app_manager.updateState(common.AppState.PostStart)

        common.doctor.saveStatus()

        common.app_manager.updateState(common.AppState.Loaded)

    def initUI(self):
        common.app_manager.updateState(common.AppState.WindowInit)
        # self.dock = QDockWidget()
        # self.dock.setMaximumWidth(300)
        # self.dock.setMaximumHeight(300)
        self.twrapper = QWidget(parent=self)
        self.twrapper.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.toolbar = QWidget(parent=self.twrapper)
        self.toolbar.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.toolbar.setStyleSheet(
            "background-color: " + self.rc.common_config["bgWheelColor"] + ";"
        )
        self.tools_layout = QVBoxLayout()

        self.settingsButton = QPushButton("", default=False, autoDefault=False)
        self.settingsButton.setStyleSheet("border-style: none;")
        self.exitButton = QPushButton("", default=False, autoDefault=False)
        self.exitButton.setStyleSheet("border-style: none;")

        self.settingsButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.exitButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # self.dock.setWidget(self.settingsButton)
        # self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.dock)

        self.tools_layout.addWidget(self.exitButton)
        self.tools_layout.addWidget(self.settingsButton)
        self.toolbar.setLayout(self.tools_layout)

        # self.toolbar.setMaximumWidth(100)
        # self.toolbar.setMaximumHeight(200)

        self.btn_size = self.conf["window"]["geometry"][2] // 6
        self.settingsButton.setMaximumWidth(self.btn_size)
        self.settingsButton.setMaximumHeight(self.btn_size)
        self.exitButton.setMaximumWidth(self.btn_size)
        self.exitButton.setMaximumHeight(self.btn_size)
        s_pos = (
            self.conf["window"]["geometry"][2] - self.btn_size
        )  # - int(math.sqrt(2)/2 * self.conf["window"]["geometry"][2]/4)
        self.toolbar.setGeometry(
            s_pos, s_pos - self.btn_size, self.btn_size, self.btn_size * 2
        )
        # self.twrapper.addWidget(self.toolbar)

        self.setCentralWidget(self.twrapper)

        self.toolbar.hide()

        self.settingsButton.clicked.connect(self.openSettings)
        self.exitButton.clicked.connect(self.close)

        self.installEventFilter(self)

        # self.drawBlur()

    @pyqtSlot()
    def updateUi(self):
        """
        Update UI colors on settings update
        """
        self.toolbar.setStyleSheet(
            "background-color: " + self.rc.conf["toolsBackgroundColor"] + ";"
        )
        self.toolbar.style().unpolish(self.toolbar)
        self.toolbar.style().polish(self.toolbar)
        self.toolbar.update()

    @pyqtSlot()
    def updateIcons(self):
        self.settingsButton.setIcon(self.settings_icon)
        self.exitButton.setIcon(self.quit_icon)

    def postStart(self):
        """
        Initialize the UI after the root canvas has been loaded
        """
        self.settings_pixmap = QPixmap(
            os.path.join(self.rc.conf["iconsFolder"], self.rc.conf["settingsIcon"])
        )
        self.quit_pixmap = QPixmap(
            os.path.join(self.rc.conf["iconsFolder"], self.rc.conf["closeIcon"])
        )
        self.settings_icon = QIcon()
        self.quit_icon = QIcon()
        # self.settings_pixmap.width = 100
        # self.settings_pixmap.height = 100
        # self.settings_pixmap = self.settings_pixmap.scaled(QSize(100, 100), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        gui_tools.icon_managers["tools"].updated.connect(self.updateIcons)

        gui_tools.icon_managers["tools"].colorPixmap(
            self.settings_pixmap, self.settings_icon
        )
        gui_tools.icon_managers["tools"].colorPixmap(self.quit_pixmap, self.quit_icon)
        self.settingsButton.setIcon(self.settings_icon)
        self.settingsButton.setIconSize(
            QSize(int(self.btn_size // 1.5), int(self.btn_size // 1.5))
        )
        self.exitButton.setIcon(self.quit_icon)
        self.exitButton.setIconSize(
            QSize(int(self.btn_size // 1.5), int(self.btn_size // 1.5))
        )

        self.rc.conf.updated.connect(self.updateUi)

    @pyqtSlot()
    def openSettings(self):
        self.settings.show()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.HoverEnter:
            self.toolbar.show()
        elif event.type() == QEvent.Type.HoverLeave:
            self.toolbar.hide()
        return super(RootWindow, self).eventFilter(obj, event)

    def drawBlur(self):
        self.blur_widget = QWidget(self)
        self.blur_widget.setGeometry(0, 0, *self.conf.c["window"]["geometry"][2:])
        self.blur_widget.setStyleSheet(
            "border-radius: {}px;\
                                       border: 0px solid white;\
                                       background-color: rgba(0, 0, 0, 0.5);".format(
                self.conf.c["window"]["geometry"][2] / 6
            )
        )
        # self.blur_widget.
        self.blur_filter = QGraphicsBlurEffect()
        self.blur_filter.setBlurRadius(15)
        os.system(
            "xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id "
            + str(int(self.winId()))
        )
        # self.blur_widget.setGraphicsEffect(self.blur_filter)
        self.blur_widget.show()

    def paintEvent(self, event):
        self.qp = QPainter(self)
        self.qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        # self.qp.begin(self)
        self.draw()
        self.qp.end()

    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            point = self.pos().toPointF() + event.globalPosition() - self.dragPos
            self.move(point.toPoint())
            self.dragPos = event.globalPosition()
            event.accept()

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
            self.conf.c["canvas"]["modules"][0]["class"].processKey(True)
        elif event.key() == QtCore.Qt.Key_A:
            self.conf.c["canvas"]["modules"][0]["class"].processKey(False)
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
        common.app_manager.updateState(common.AppState.SerialInit)

        self.serialModules = {}
        self.serialModulesNames = []

        for i in self.conf.c["canvas"]["serialModulesLoad"]:
            mod_name = self.conf.c["canvas"]["serialModules"][i]["name"]
            mod = importlib.import_module("smartwheel." + mod_name)

            try:
                cls = mod.SConn(
                    os.path.join(
                        self.conf["config_dir"],
                        self.conf.c["canvas"]["serialConfigDir"],
                        self.conf.c["canvas"]["serialModules"][i]["config"],
                    ),
                    self.rc.ae.callAction,
                )
                cls.start()
                self.serialModules[mod_name] = cls
                self.serialModulesNames.append(mod_name)
            except BaseException as e:
                self.logger.error("Failed to load " + mod_name + ": " + str(e))

    def loadClasses(self):
        self.rc = RootCanvas(
            self.conf.c_canvas, self.conf.launch_config["config_dir"], self.update
        )

        QGuiApplication.instance().aboutToQuit.connect(self.rc.killThreads)

    def draw(self):
        self.rc.draw(self.qp)


def main():
    dirpath = os.path.dirname(os.path.realpath(__file__))
    launch = os.path.join(dirpath, "launch.json")

    if not os.path.exists(launch):
        print(
            "Please check that configuration files are present in the installation directory"
        )
        return

    with open(launch, "r") as f:
        launch_config = json.load(f)

    common.defaults_manager.postInit(
        launch_config["config_dir"], launch_config["defaults_config_dir"]
    )

    launch_config["config_dir"] = os.path.join(dirpath, launch_config["config_dir"])
    launch_config["defaults_config_dir"] = os.path.join(
        dirpath, launch_config["defaults_config_dir"]
    )

    status = os.path.join(dirpath, "status.json")
    common.doctor.loadStatus(status)

    main_conf_path = os.path.join(launch_config["config_dir"], "config.json")
    conf = WConfig(main_conf_path, launch_config)
    conf["config_dir"] = launch_config["config_dir"]
    conf["basedir"] = dirpath
    conf.c_canvas["basedir"] = conf["basedir"]
    root = RootWindow(conf)
    sys.exit(root.app.exec())


if __name__ == "__main__":
    main()

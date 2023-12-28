from PyQt6.QtCore import pyqtSignal, QPoint
from PyQt6.QtGui import QPen, QBrush, QColor

from smartwheel import config, gui_tools
from smartwheel.tools import merge_dicts
from smartwheel.ui.base import BaseUIElem
from smartwheel.api.action import CommandActions

import rtmidi
from rtmidi.midiconstants import CONTROL_CHANGE

class UIElem(BaseUIElem):
    updateSignal = pyqtSignal()

    def __init__(self, config_file, WConfig):
        super().__init__()
        self.config_file = config_file
        self.loadConfig()
        merge_dicts(self.conf, WConfig)
        self.icon_path = self.conf["icon_path"]

        self.min_pos = 0
        self.max_pos = 127
        self.cur = 0
        self.initGUI()

    def __del__(self):
        self.midiout.close_port()
        del self.midiout

    def loadConfig(self):
        self.conf = config.Config(self.config_file, varsWhitelist=["haptics"])
        self.conf.loadConfig()

    def initGUI(self):
        self.midiout = rtmidi.MidiOut()

        if not self.conf["enableVirtualPort"]:
            if not self.midiout.get_ports():
                return
            self.midiout.open_port(self.conf["port"])
        else:
            self.midiout.open_virtual_port(self.conf["virtualPortName"])

    def processKey(self, event, pulse):
        if not pulse.click:
            return

        if not self.midiout.is_port_open():
            return
        if event["call"] == CommandActions.scroll:
            if pulse.up:
                self.cur = min(self.max_pos, self.cur + self.conf["steps"])
            else:
                self.cur = max(self.min_pos, self.cur - self.conf["steps"])

        self.midiout.send_message([CONTROL_CHANGE, self.conf["controlChangeType"], self.cur])

    def draw(self, qp, offset=None):
        pen = QPen(QColor(self.conf["indicatorColor"]))
        brush = QBrush(QColor(self.conf["indicatorColor"]))
        qp.setPen(pen)
        qp.setBrush(brush)
        qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), self.cur // 4, self.cur // 4)
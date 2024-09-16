import errno

from smartwheel import config
from smartwheel.ui.base import BaseUIElem
from smartwheel.tools import merge_dicts
from smartwheel.api.action import CommandActions, Pulse
import socket
import math
import logging
from queue import Queue
import weakref
import datetime

from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QRect, pyqtSlot, QTimer, QObject, QPointF


class SDRInfo:
    frequency: float = None
    frequency_hz: int = None
    unit: str = None

    def to_str(self) -> str:
        return "--" if self.frequency is None else "{:.3f} {}".format(self.frequency, self.unit)

    def from_hz(self, hz: int):
        self.frequency_hz = hz
        if hz < 1000:
            self.frequency = hz
            self.unit = "Hz"
        elif hz < 1000*1000:
            self.frequency = hz / 1000.0
            self.unit = "KHz"
        elif hz < 1000*1000*1000:
            self.frequency = hz / 1000000.0
            self.unit = "MHz"
        else:
            self.frequency = hz / 1000000000.0
            self.unit = "GHz"

class UIElem(BaseUIElem):
    def __init__(self, config_file: str, WConfig: config.Config):
        super().__init__()
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.loadConfig()
        self.icon_path = self.conf["icon_path"]
        merge_dicts(self.conf, WConfig)
        self.quant = []
        self.conf["debug"] = {}
        self.conf.updated.connect(self.updateCache)
        self.updateVars()
        self.updateCache()
        self.last_quant = 0
        self.last_angle = 0.0
        self.plugin = GQRXPlugin(weakref.ref(self.conf))

    def loadConfig(self):
        self.conf = config.Config(self.config_file)
        self.conf.loadConfig()

    def updateVars(self, offset=0):
        self.text_width = ((self.conf["width"] + offset) * 3) // 4
        self.text_height = (self.conf["height"] + offset) // 8

    @pyqtSlot()
    def updateCache(self):
        if not self.processFrequencyQuant():
            msg = QMessageBox()
            msg.setWindowTitle("SDR Module")
            msg.setText("Failed to parse frequencies list: " + self.conf["frequencyQuant"] + " must be separated with ;")
            msg.exec()
        self.conf["debug"]["quantList"] = self.quant
        self.processFreqStep()

    def processFreqStep(self):
        self.step = self.conf["maxScrollSpeed"] / len(self.quant)

    def processFrequencyQuant(self) -> bool:
        quant_default = [1000]  # 1 khz
        quant_new = []
        for x in self.conf["frequencyQuant"].split(';'):
            x = x.strip()
            if not x:
                continue

            try:
                quant_new.append(float(x))
            except ValueError:
                if not self.quant:
                    self.quant = quant_default
                return False

        if not quant_new and not self.quant:
            self.quant = quant_default
            return False
        self.quant = quant_new  # Apply changes
        return True

    def draw_speed_overlay(self, qp: QPainter, offset=None):
        pen_accent = QPen(QColor(self.conf["bgWheelColor"]))
        brush_accent = QBrush(QColor(self.conf["bgWheelColor"]))
        pen = QPen(QColor(self.conf["bgWheelColor"]))
        pen.setWidthF(self.conf["freqDotLineWidth"])

        if len(self.quant) % 2 == 0:
            n = max(len(self.quant) - 1, 1) / 2.0
        else:
            n = len(self.quant) // 2

        for i in range(len(self.quant)):
            if i <= self.last_quant:
                qp.setPen(pen_accent)
                qp.setBrush(brush_accent)
            else:
                qp.setPen(pen)
                qp.setBrush(Qt.BrushStyle.NoBrush)

            x_offset = (i - n) * 2.0 * self.conf["freqDotRadius"] * self.conf["freqDotSpacing"]
            qp.drawEllipse(QPointF(self.conf["cx"] + x_offset, (self.conf["cy"] * 4) // 3 + offset // 8),
                           self.conf["freqDotRadius"], self.conf["freqDotRadius"])

        qp.setPen(pen_accent)
        qp.setBrush(brush_accent)
        qp.drawEllipse(QPointF(self.conf["cx"] + math.cos(math.radians(self.last_angle * self.conf["angleDotSpeedMul"])) * (self.conf["width"] // 2 - self.conf["angleDotOffset"] + offset / 2.0),
                               self.conf["cy"] + math.sin(math.radians(self.last_angle * self.conf["angleDotSpeedMul"])) * (self.conf["height"] // 2 - self.conf["angleDotOffset"] + offset / 2.0)), self.conf["angleDotRadius"], self.conf["angleDotRadius"])

    def draw(self, qp: QPainter, offset=None):
        pen = QPen(QColor(self.conf["majorTextColor"]))
        # max_offset = (self.conf["width"]) / 4.0  # TODO move to common
        font = QFont(self.conf["frequencyFont"], self.conf["frequencyFontSize"])
        # font.setPointSizeF(float(self.conf["frequencyFontSize"]) - (((max_offset - offset) / max_offset) * 2.0))
        qp.setPen(pen)
        qp.setFont(font)
        qp.drawText(QRect(self.conf["cx"] - self.text_width // 2, self.conf["cy"] - self.text_height // 2,
                          self.text_width, self.text_height), Qt.AlignmentFlag.AlignCenter, self.plugin.info.to_str())
        self.draw_speed_overlay(qp, offset)

    def processKey(self, event: dict, pulse: Pulse):
        quant = min(int(abs(pulse.velocity) / self.step), len(self.quant) - 1)
        self.last_angle = pulse.step
        if pulse.velocity == 0.0:
            self.last_quant = 0

        if not pulse.click:
            return

        if event["call"] == CommandActions.scroll:
            self.last_quant = quant
            freq = self.quant[quant] * (1 if pulse.up else -1)  # quantized
            self.conf["debug"]["lastFreqStep"] = freq
            self.conf["debug"]["lastVel"] = pulse.velocity
            self.logger.debug("Set frequency " + str(freq) + " Hz" + "; vel: " + str(pulse.velocity))
            self.plugin.set_freq_delta(freq)


class GQRXPlugin(QObject):
    info = SDRInfo()

    def __init__(self, conf: weakref.ref):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.conf = conf
        addr_port = self.conf()["gqrx"]["listenerAddr"].split(':')
        try:
            self.addr = addr_port[0]
            self.port = int(addr_port[1])
        except ValueError:
            self.logger.error("Wrong server address:port : " + self.conf()["gqrx"]["listenerAddr"])
            self.addr = "127.0.0.1"
            self.port = 0
        # self.info.frequency = 100.0
        # self.info.unit = "MHz"
        self.timer = QTimer(self)
        self.timer.setInterval(self.conf()["gqrx"]["pollingRate"])
        self.timer.timeout.connect(self.run)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.connected = False
        self.msgs = Queue()
        self.freq_cmd = None
        self.freq_set_time = datetime.datetime.utcfromtimestamp(0)
        self.timer.start()

    @pyqtSlot()
    def run(self):
        self.connect()
        if self.connected:
            self.recv()
            self.process_cmd_queue()

    def process_cmd_queue(self):
        # Send next cmd
        if self.freq_cmd is not None:
            self.msgs.put(self.freq_cmd)
            self.freq_cmd = None
            self.freq_set_time = datetime.datetime.now()
        if not self.msgs.empty():
            self.send_to_socket(self.msgs.get())
        # No frequency input
        if datetime.datetime.now() - self.freq_set_time >= datetime.timedelta(milliseconds=self.conf()["gqrx"]["freqFetchTimeout"]):
            self.add_cmd_to_queue("f")

    def connect(self):
        if self.connected:
            return
        try:
            self.sock.connect((self.addr, self.port))
        except socket.error as e:
            self.conf()["debug"]["socketErrno"] = str(e)
            self.conf()["debug"]["connected"] = False
            if not e.args[0] == errno.EISCONN:
                self.connected = False
                self.logger.debug("gqrx : conn refused : " + str(e))
                return
        self.conf()["debug"]["socketErrno"] = None
        self.conf()["debug"]["connected"] = True
        self.connected = True
        self.logger.debug("gqrx : online!!!")

    def send_to_socket(self, msg: str):
        msg += '\n'
        try:
            self.sock.sendall(msg.encode("utf-8"))
        except socket.error as e:
            self.connected = False

    def add_cmd_to_queue(self, msg: str):
        self.msgs.put(msg)

    def recv(self):
        res_data = bytes()
        while True:
            try:
                data = self.sock.recv(1024)
            except socket.error as e:
                if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
                    break
                self.logger.debug("gqrx : recv failed : " + str(e))
                self.connected = False
                return

            if not data:
                break  # End of data
            res_data += data

        if res_data:
            self.parse_cmd(res_data.decode('utf-8'))

    def parse_cmd(self, cmd: str):
        commands = cmd.split('\n')
        for c in commands:
            c_s = c.strip()
            if not c_s:
                continue

            if c_s == "RPRT 0":
                pass  # Command ok
            else:
                try:
                    hz = int(c_s)
                    self.info.from_hz(hz)
                except ValueError:
                    # Unknown cmd
                    self.logger.warning("gqrx : unknown cmd : " + c_s)

    def set_freq_delta(self, delta_hz: int):
        if self.info.frequency_hz is None:
            return
        self.info.from_hz(self.info.frequency_hz + delta_hz)
        cmd = "F " + str(self.info.frequency_hz)
        # self.add_cmd_to_queue(cmd)
        self.freq_cmd = cmd

    def __del__(self):
        self.sock.close()
        pass  # TODO send close signal and disconnect


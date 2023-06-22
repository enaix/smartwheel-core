import logging
import os
import sys
import queue
import socket
import time

from PyQt6.QtCore import *

from smartwheel.ui.internal.baseinternal import BaseInternal
from smartwheel import config 


class Internal(BaseInternal):
    sendSignal = pyqtSignal(str)
    mutex = QMutex()
    wake = QWaitCondition()
    name = "kritaServer"

    def __init__(self, WConfig, config_file):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.sendSignal.connect(self.send)
        self.signals = {"send": self.sendSignal}
        self.config_file = config_file
        self.conf = WConfig
        self.loadConfig()
        self.data = queue.SimpleQueue()
        self.socket_addr = "/tmp/krita_socket"
        self.socket_type = None
        self.sock = None

    def __del__(self):
        if hasattr(self, "sock"):
            self.sock.close()

    def loadConfig(self):
        self.conf = config.Config(config_file=self.config_file)
        self.conf.loadConfig()

    def getSignals(self):
        return self.signals

    def run(self):
        ok = self.open_socket()
        if not ok:
            self.logger.warning("Cannot open krita socket")
            return
        while True:
            self.sendData(self.data.get())

    def open_socket(self):
        if sys.platform == 'linux':
            self.socket_type = socket.AF_UNIX
            if os.path.exists(str(self.socket_addr)):
                os.remove(str(self.socket_addr))

        else:
            self.socket_addr = ("127.0.0.1", 34782)
            self.socket_type = socket.AF_INET

        self.sock = socket.socket(self.socket_type, socket.SOCK_STREAM)
        self.sock.settimeout(self.conf["socketTimeout"])
        while self.isRunning:
            try:
                self.sock.bind(self.socket_addr)
                self.sock.listen()
                return True
            except BaseException as e:
                self.logger.error(e)
                time.sleep(self.conf["errorTimeout"])

    @pyqtSlot(str)
    def send(self, data):
        self.data.put(data)  # queue is thread safe

    def sendData(self, data):
        self.logger.debug(data)
        try:
            if not hasattr(self, "conn"):
                self.conn, _ = self.sock.accept()
            self.conn.sendall(data.encode("utf-8"))
        except BaseException as e:
            try:
                self.conn, _ = self.sock.accept()
            except BaseException as ex:
                self.logger.error(ex)
                return
            self.logger.error(e)

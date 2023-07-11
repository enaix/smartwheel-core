import logging

import serial
from PyQt6.QtCore import *

from smartwheel import config
from smartwheel.serialpipe.base import ConnPipe
from smartwheel.api.app import Classes
from smartwheel.api.action import DevicePulse, PulseTypes


class SConn(ConnPipe):
    """Default serial connection interface (compatible with pico)"""

    def __init__(self, config_file):
        super().__init__()
        self.conf = None
        self.config_file = config_file
        self.call = Classes.ActionEngine().callAction
        self.logger = logging.getLogger(__name__)
        self.loadConfig()

    def loadConfig(self):
        self.conf = config.Config(
            config_file=self.config_file, logger=self.logger, varsWhitelist=["binds"]
        )
        self.conf.loadConfig()

    def serialCall(self, string):
        """
        Parse serial call from string

        Parameters
        ----------
        string
            Command from serial
        """
        # l = string.split()
        string = string.decode("utf-8").strip()
        print(string)
        if string == "":
            return
        cmd = []
        for b in self.conf["binds"]:
            for c in b["commands"]:
                if c["string"] == string:
                    pulse = DevicePulse()
                    pulse.bind = b["name"]
                    pulse.command = c["string"]

                    if b["type"] == "button":
                        pulse.type = PulseTypes.BUTTON
                    else:
                        pulse.type = PulseTypes.ENCODER

                    cmd.append(pulse)

        if cmd != []:
            for c in cmd:
                self.call.emit(c)

    def run(self):
        """
        Reads for serial data from device and executes actions
        """
        # TODO move to another module
        tm = None
        if self.conf["useTimeout"]:
            tm = self.conf["timeout"]
        try:
            with serial.Serial(
                self.conf["device"], self.conf["baudRate"], timeout=tm
            ) as s:
                while self.isRunning() and s.is_open:
                    self.serialCall(s.readline())
        except BaseException as e:
            self.logger.error(e)
            return

from serialpipe.base import ConnPipe
from PyQt5.QtCore import *
import serial
import json

class SConn(ConnPipe):
    def __init__(self, config_file, call_signal):
        super().__init__()
        self.config_file = config_file
        self.call = call_signal
        self.loadConfig()

    def loadConfig(self):
        with open(self.config_file, "r") as f:
            self.conf = json.load(f)

    def call_action(self, cmd, state):
        pass

    def serialCall(self, string):
        #l = string.split()
        string = string.decode("utf-8").strip()
        print(string)
        if string == '':
            return
        cmd = []
        for b in self.conf["binds"]:
            for c in b["commands"]:
                if c["string"] == string:
                    cmd.append((b, c))
        if cmd != []:
            for c in cmd:
                if c != []:
                    self.call.emit(c)

    def run(self):
        # TODO move to another module
        tm = None
        if self.conf["useTimeout"]:
            tm = self.conf["timeout"]
        try:
            with serial.Serial(self.conf["device"], self.conf["baudRate"], timeout=tm) as s:
                while self.isRunning() and s.is_open:
                    self.serialCall(s.readline())
        except BaseException as e:
            print(e)
            return


import config
from PyQt6.QtCore import *

from smartwheel.serialpipe.base import ConnPipe


class SConn(ConnPipe):
    """Control the wheel from keypresses (no background scanner)"""

    def __init__(self, config_file, call_signal):
        """
        Initialize keyboardpipe

        Parameters
        ----------
        config_file
            Configuration file
        call_signal
            Actionegnine signal to call
        """
        super().__init__()
        self.conf = None
        self.config_file = config_file
        self.call = call_signal
        self.loadConfig()

    def loadConfig(self):
        self.conf = config.Config(self.config_file)
        self.conf.loadConfig()

    def findKey(self, key):
        """
        Returns command tuple by key

        Parameters
        ----------
        key
            String containing the key
        """
        for b in self.conf["binds"]:
            for c in b["commands"]:
                if c["string"] == key:
                    return b, c

        return None

    def handleKeypress(self, event):
        """
        Keypress handler, called from main thread
        """
        if event.key() == Qt.Key_W:
            self.call.emit(self.findKey("w"))
        elif event.key() == Qt.Key_A:
            self.call.emit(self.findKey("a"))
        elif event.key() == Qt.Key_Up:
            self.call.emit(self.findKey("up"))
        elif event.key() == Qt.Key_Down:
            self.call.emit(self.findKey("down"))
        elif event.key() == Qt.Key_Return:
            self.call.emit(self.findKey("return"))
        elif event.key() == Qt.Key_Escape:
            self.call.emit(self.findKey("esc"))

    def run(self):
        """
        We don't need the run loop, since we are reading keyboard events straight from Qt
        """
        pass

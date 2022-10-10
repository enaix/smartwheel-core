from serialpipe.base import ConnPipe, PRButton, ClickButton, Rotary
from PyQt5.QtCore import *
import json
from pynput import keyboard


class BGKeyboard(ConnPipe):
    """Background keyboard listener"""

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
        self.keys = None
        self.conf = None
        self.config_file = config_file
        self.call = call_signal
        self.loadConfig()
        self.loadKeys()

    def loadConfig(self):
        with open(self.config_file, "r") as f:
            self.conf = json.load(f)

    def loadKeys(self):
        """
        Initialize dicts of keys to quickly find them
        """
        self.keys = {"keyboards": {}, "prbuttons": {}, "clickbuttons": {}, "encoders": {}}
        self.prbuttons = {}
        self.clickbuttons = {}
        self.encoders = {}

        for kbs in self.conf["keyboards"]:
            for k in kbs["keys"]:
                self.keys["keyboards"][k["string"]] = kbs

        for btn in self.conf["prbuttons"]:
            self.keys["prbuttons"][btn["key"]] = btn
            self.prbuttons[btn["name"]] = PRButton(btn["threshold"])
            self.prbuttons[btn["name"]].setupCallbacks([self.call] * 3,
                                                       [({"name": btn["name"]}, x) for x in
                                                        ["press", "click", "doubleclick"]])

        for btn in self.conf["clickbuttons"]:
            self.keys["clickbuttons"][btn["key"]] = btn
            self.clickbuttons[btn["name"]] = ClickButton(btn["threshold"])
            self.clickbuttons[btn["name"]].setupCallbacks([self.call] * 2,
                                                          [({"name": btn["name"]}, x) for x in
                                                           ["click", "doubleclick"]])

        for enc in self.conf["encoders"]:
            self.keys["encoders"][enc["keyUp"]] = (enc, True)  # up
            self.keys["encoders"][enc["keyDown"]] = (enc, False)  # down
            self.encoders[enc["name"]] = Rotary(enc["linkedButton"])
            self.encoders[enc["name"]].setupCallbacks([self.call] * 6,
                                                      [({"name": enc["name"]}, x) for x in
                                                       ["up", "down", "click up",
                                                        "click down", "double up", "double down"]])

    def on_press(self, key):
        """
        Pynput on press event

        Parameters
        ----------
        key
            Key object
        """
        if self.keys["prbuttons"][key.name] is not None:
            btn = self.keys["prbuttons"][key.name]
            self.prbuttons[btn["name"]].press(True)

    def on_release(self, key):
        """
        Pynput on release event

        Parameters
        ----------
        key
            Key object
        """
        if self.keys["keyboards"][key.name] is not None:
            btn = self.keys["keyboards"][key.name]
            self.call.emit((btn["name"], key.name))

        if self.keys["clickbuttons"][key.name] is not None:
            btn = self.keys["clickbuttons"][key.name]
            self.clickbuttons[btn["name"]].press()

        if self.keys["encoders"][key.name] is not None:
            enc, up = self.keys["encoders"][key.name]
            self.encoders[enc["name"]].rotate(up)

    def run(self):
        """
        The main listener loop
        """
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

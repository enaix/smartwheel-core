import logging

from pynput import keyboard
from PyQt6.QtCore import *

from smartwheel import config
from smartwheel.serialpipe.base import ClickButton, ConnPipe, PRButton, Rotary


class SConn(ConnPipe):
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
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.call = call_signal
        self.loadConfig()
        self.loadKeys()

    def loadConfig(self):
        self.conf = config.Config(config_file=self.config_file, logger=self.logger)
        self.conf.loadConfig()

    def loadKeys(self):
        """
        Initialize dicts of keys to quickly find them
        """
        self.keys = {
            "keyboards": {},
            "prbuttons": {},
            "clickbuttons": {},
            "encoders": {},
        }
        self.prbuttons = {}
        self.clickbuttons = {}
        self.encoders = {}

        for kbs in self.conf["keyboards"]:
            for k in kbs["keys"]:
                self.keys["keyboards"][k["string"]] = (kbs, k)

        for btn in self.conf["prbuttons"]:
            self.keys["prbuttons"][btn["key"]] = btn
            self.prbuttons[btn["name"]] = PRButton(btn["threshold"])
            self.prbuttons[btn["name"]].setupCallbacks(
                [self.call] * 3,
                [(btn, {"string": x}) for x in ["press", "click", "doubleclick"]],
            )

        for btn in self.conf["clickbuttons"]:
            self.keys["clickbuttons"][btn["key"]] = btn
            self.clickbuttons[btn["name"]] = ClickButton(btn["threshold"])
            self.clickbuttons[btn["name"]].setupCallbacks(
                [self.call] * 2,
                [(btn, {"string": x}) for x in ["click", "doubleclick"]],
            )

        for enc in self.conf["encoders"]:
            self.keys["encoders"][enc["keyUp"]] = (enc, True)  # up
            self.keys["encoders"][enc["keyDown"]] = (enc, False)  # down

            if (
                enc["linkedButton"] is not None
                and self.prbuttons.get(enc["linkedButton"]) is None
            ):
                self.logger.error(
                    "Could not link "
                    + enc["name"]
                    + " with non-existent prbutton "
                    + enc["linkedButton"]
                )

            self.encoders[enc["name"]] = Rotary(self.prbuttons[enc["linkedButton"]])
            self.encoders[enc["name"]].setupCallbacks(
                [self.call] * 6,
                [
                    (enc, {"string": x})
                    for x in [
                        "up",
                        "down",
                        "click up",
                        "click down",
                        "double up",
                        "double down",
                    ]
                ],
            )

    def on_press(self, key):
        """
        Pynput on press event

        Parameters
        ----------
        key
            Key object
        """
        k = str(key).strip("'")

        if self.keys["keyboards"].get(k) is not None:
            kb, btn = self.keys["keyboards"][k]
            self.call.emit((kb, btn))

        if self.keys["prbuttons"].get(k) is not None:
            btn = self.keys["prbuttons"][k]
            self.prbuttons[btn["name"]].execPress(True)

    def on_release(self, key):
        """
        Pynput on release event

        Parameters
        ----------
        key
            Key object
        """
        k = str(key).strip("'")

        if self.keys["prbuttons"].get(k) is not None:
            btn = self.keys["prbuttons"][k]
            self.prbuttons[btn["name"]].execPress(False)

        if self.keys["clickbuttons"].get(k) is not None:
            btn = self.keys["clickbuttons"][k]
            self.clickbuttons[btn["name"]].execPress()

        if self.keys["encoders"].get(k) is not None:
            enc, up = self.keys["encoders"][k]
            self.encoders[enc["name"]].execRotate(up)  # TODO add audio keys workaround

    def run(self):
        """
        The main listener loop
        """
        with keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        ) as listener:
            listener.join()

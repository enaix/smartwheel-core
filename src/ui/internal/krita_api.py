import json

from PyQt5.QtCore import pyqtSignal, pyqtSlot

from ui.internal.baseinternal import BaseInternal


class Internal(BaseInternal):
    def __init__(self, WConfig, config_file):
        super().__init__()
        self.name = "kritaAPI"

    def setColor(self, r, g, b):
        call = {"action": "set_color"}
        call["properties"] = {"rgb": [r, g, b]}
        return json.dumps(call)

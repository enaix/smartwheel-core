import json

from PyQt6.QtCore import pyqtSignal, pyqtSlot

from smartwheel.ui.internal.baseinternal import BaseInternal


class Internal(BaseInternal):
    name = "kritaAPI"
    
    def __init__(self, WConfig, config_file):
        super().__init__()

    def setColor(self, r, g, b):
        call = {"action": "set_color"}
        call["properties"] = {"rgb": [r, g, b]}
        return json.dumps(call)

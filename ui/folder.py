from ui.base import BaseUIElem
import json

class UIElem(BaseUIElem):
    def __init__(self, config_file, WConfig):
        super().__init__()
        self.is_folder = True
        self.loadConfig(config_file)
        self.conf = {**self.conf, **WConfig}
        self.icon_path = self.conf.get("iconPath", None)
        self.modules = self.conf["modules"]
        self.wrapper_pointer = None

    def loadConfig(self, config_file):
        with open(config_file, 'r') as f:
            self.conf = json.load(f)

    def processKey(self, event):
        event["canvas"]().reloadWheelModules(False, self.wrapper_pointer()) # call canvas module

    def draw(self, qp, offset):
        pass


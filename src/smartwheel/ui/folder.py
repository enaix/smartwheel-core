from smartwheel import config
from smartwheel.ui.base import BaseUIElem


class UIElem(BaseUIElem):
    def __init__(self, config_file, WConfig):
        super().__init__()
        self.is_folder = True
        self.config_file = config_file
        self.loadConfig()
        self.conf.c = {**self.conf, **WConfig}
        self.icon_path = self.conf.get("iconPath", None)
        self.modules = self.conf["modules"]
        self.wrapper_pointer = None

    def loadConfig(self):
        self.conf = config.Config(config_file=self.config_file)
        self.conf.loadConfig()

    def processKey(self, event):
        event["canvas"]().reloadWheelModules(
            False, self.wrapper_pointer()
        )  # call canvas module

    def draw(self, qp, offset=None):
        pass

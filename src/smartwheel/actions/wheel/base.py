from PyQt6.QtCore import QObject
from smartwheel.api.action import Pulse


class BaseWheelAction(QObject):
    def __init__(self):
        super(BaseWheelAction, self).__init__()

    def run(self, action: str, pulse: Pulse):
        pass

from PyQt6.QtCore import QObject
from smartwheel.api.action import Pulse


class BaseAction(QObject):
    def __init__(self):
        super(BaseAction, self).__init__()

    def run(self, context: dict, pulse: Pulse):
        pass

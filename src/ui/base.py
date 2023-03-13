# from PyQt6.QtGui import *
from PyQt6.QtCore import QObject


class BaseUIElem(QObject):
    def __init__(self):
        super().__init__()
        pass

    def loadConfig(self):
        pass

    def draw(self, qp, offset=None):
        pass

#from PyQt5.QtGui import *
from PyQt5.QtCore import *

class BaseUIElem(QObject):
    def __init__(self):
        super().__init__()
        pass

    def loadConfig(self):
        pass
    
    def draw(self):
        pass

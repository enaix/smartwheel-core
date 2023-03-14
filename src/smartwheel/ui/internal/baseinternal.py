from PyQt6.QtCore import QThread


class BaseInternal(QThread):
    def __init__(self):
        super().__init__()
        self.name = "baseInternal"
        self.signals = {}

    def __del__(self):
        pass

    def getSignals(self):
        return self.signals

    def run(self):
        pass

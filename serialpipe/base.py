from PyQt5.QtCore import QThread


class ConnPipe(QThread):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        pass

    def __del__(self):
        self.wait()

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal


class ConfigManager(QObject):
    """
    Global class that manages all config files
    """
    save = pyqtSignal()

    def __init__(self):
        super(ConfigManager, self).__init__()
    
    @pyqtSlot()
    def saveConfig(self):
        self.save.emit()


config_manager = ConfigManager()

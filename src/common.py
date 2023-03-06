from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class ConfigManager(QObject):
    """
    Global class that manages all config files. This module contains an instance of this class, acting as a singleton
    """

    save = pyqtSignal()

    def __init__(self):
        super(ConfigManager, self).__init__()

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(ConfigManager, cls).__new__(cls)
        return cls.instance

    @pyqtSlot()
    def saveConfig(self):
        """
        Slot function that executes the saving of all Config objects, must be called from settings module
        """
        self.save.emit()


config_manager = ConfigManager()

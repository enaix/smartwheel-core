import json
import os

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


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


class CacheManager(QObject):
    """
    Global class that manages cache access. Not inteded to be called from other threads
    """

    def __init__(self):
        super(CacheManager, self).__init__()

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(CacheManager, cls).__new__(cls)
        return cls.instance

    def initManager(self, conf):
        self.conf = conf

        if not os.path.exists(self.conf["cacheDir"]):
            os.mkdir(self.conf["cacheDir"])

    def load(self, app_name, filename):
        """
        Load cache file path and config (optional) from cache. Returns (True, filepath, conf) if found

        Parameters
        ==========
        app_name
            Application name, must be unique
        filename
            File to load
        """
        if self.conf is None:
            print("Cache manager is not initialized")
            return False, None, None

        appdir = os.path.join(self.conf["cacheDir"], app_name)
        if not os.path.exists(appdir):
            os.mkdir(appdir)

        cachepath = os.path.join(appdir, filename)
        confpath = os.path.join(appdir, filename.split(".")[0] + ".json")
        cacheconf = None

        if not os.path.exists(cachepath):
            return False, None, None

        if os.path.exists(confpath):
            with open(confpath, "r") as f:
                cacheconf = json.load(f)

        return True, cachepath, cacheconf

    def save(self, app_name, filename, conf=None):
        """
        Save to cache. Returns cache filepath to save manually. Note that config object is saved and loaded automatically

        Parameters
        ==========
        app_name
            Application name, must be unique
        filename
            File to save
        conf
            (Optional) Cache metadata
        """
        if self.conf is None:
            print("Cache manager is not initialized")
            return None

        appdir = os.path.join(self.conf["cacheDir"], app_name)
        if not os.path.exists(appdir):
            os.mkdir(appdir)

        cachepath = os.path.join(appdir, filename)
        confpath = os.path.join(appdir, filename.split(".")[0] + ".json")

        if conf is not None:
            with open(confpath, "w") as f:
                if type(conf) == dict:
                    json.dump(conf, f)
                else:
                    json.dump(conf.c, f)

        return cachepath


config_manager = ConfigManager()
cache_manager = CacheManager()

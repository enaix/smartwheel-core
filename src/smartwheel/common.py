import json
import logging
import os
import time
from enum import auto, IntEnum, Enum

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from smartwheel import config


class ConfigManager(QObject):
    """
    Global class that manages all config files. This module contains an instance of this class, acting as a singleton
    """

    save = pyqtSignal()
    updated = pyqtSignal(str)
    batchUpdate = pyqtSignal(list)

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


class AppState(IntEnum):
    PreStart = 0
    InternalModulesInit = 1
    BrushesInit = 2
    ModulesInit = 3
    WheelInit = 4
    ActionsInit = 5
    SerialInit = 6
    WindowInit = 7
    SettingsRegistryInit = 8
    SettingsHandlersInit = 9
    SettingsInit = 10
    PostStart = 11
    Loaded = 12


class SignalWrapper(QObject):
    """
    Wrapper class that contains unique signal
    """

    signal = pyqtSignal()


class ApplicationManager(QObject):
    """
    Global class that reports application startup status

    Emits global stateChanged(state) signal and individual self.<state>.signal signals
    """

    state = AppState.PreStart
    stateChanged = pyqtSignal(int)
    # startupSignals = [pyqtSignal() for _ in AppState]

    def __init__(self):
        super(ApplicationManager, self).__init__()
        self.logger = logging.getLogger(__name__)

        for i in AppState:
            setattr(self, i.name, SignalWrapper())
        self.Loaded.signal.connect(self.loadComplete)

        self.stage_time = time.time_ns()
        self.total_time = self.stage_time

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(ApplicationManager, cls).__new__(cls)
        return cls.instance

    def updateState(self, state):
        """
        Set current startup state

        Parameters
        ==========
        state
            AppState.<state> enum
        """
        self.state = state
        self.stateChanged.emit(self.state)
        getattr(self, self.state.name).signal.emit()

        if self.state == 0:
            return
        new_time = time.time_ns()
        self.logger.info(
            "Init: "
            + AppState(self.state - 1).name
            + " took "
            + str((new_time - self.stage_time) // 1000000)
            + " ms"
        )
        self.stage_time = new_time

    @pyqtSlot()
    def loadComplete(self):
        final_time = (time.time_ns() - self.total_time) // 1000000
        self.logger.info(
            "Init: load complete. Total load time is " + str(final_time) + " ms"
        )


class StartupMode(str, Enum):
    Normal = auto()
    Update = auto()
    PostUpdate = auto()
    Defaults = auto()
    PostDefaults = auto()


class Doctor(QObject):
    """
    Medic! This class handles errors and startup modes
    """
    def __init__(self):
        super(Doctor, self).__init__()
        self.startupMode = StartupMode.Normal
        self.file = None
        self.logger = logging.getLogger(__name__)

    def saveStatus(self):
        """
        Save current startup status to the file
        """
        if self.startupMode == StartupMode.Normal:
            if os.path.exists(self.file):
                os.remove(self.file)
                return
        else:
            status = {"startupMode": self.startupMode.value, "update": False}
            with open(self.file, "w") as f:
                json.dump(status, f, indent=4)

    def loadStatus(self, file):
        """
        Load previous startup status from file

        Parameters
        ==========
        file
            Input filename
        """
        self.file = file
        if not os.path.exists(file):
            return

        try:
            with open(file, "r") as f:
                status = json.load(f)
        except BaseException:
            self.logger.error("Could not load previous startup status: file corruption. Merging defaults..")
            self.startupMode = StartupMode.Update
            return

        if status.get("update", False):
            self.startupMode = StartupMode.Update
            self.logger.warning("Note: the app has been updated. Merging the defaults")

        if status.get("startupMode") is not None:
            try:
                appStatus = StartupMode(status["startupMode"])
            except BaseException:
                self.logger.warning("Could not decode previous startup mode")
                appStatus = StartupMode.Normal
            
            if appStatus == StartupMode.Update:
                self.startupMode = StartupMode.PostUpdate
            elif appStatus == StartupMode.Defaults:
                self.startupMode = StartupMode.PostDefaults

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(Doctor, cls).__new__(cls)
        return cls.instance


class DefaultsManager(QObject):
    """
    Global class that manages defaults for config files. Is a singleton
    """

    def __init__(self):
        super(DefaultsManager, self).__init__()

    def postInit(self, config_dir, defaults_config_dir):
        """
        Post-initialize manager

        Parameters
        ==========
        config_dir
            Common configuration file dir
        """
        self.config_dir = config_dir
        self.defaults_config_dir = defaults_config_dir

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(DefaultsManager, cls).__new__(cls)
        return cls.instance


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
        self.conf["cacheDir"] = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), self.conf["cacheDir"]
        )

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
defaults_manager = DefaultsManager()
app_manager = ApplicationManager()
cache_manager = CacheManager()
doctor = Doctor()

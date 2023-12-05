import json
import logging
import os
import time
from enum import auto, IntEnum, Enum

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QMessageBox

from smartwheel.api.app import Classes, Common


class ConfigManager(QObject):
    """
    Global class that manages all config files. This module contains an instance of this class, acting as a singleton
    """

    save = pyqtSignal()
    defaults = pyqtSignal()
    updated = pyqtSignal(str)
    batchUpdate = pyqtSignal(list)
    merge = pyqtSignal()

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
        defaults_manager.save()

    @pyqtSlot()
    def setDefaults(self):
        """
        Slot function that sets defaults for all Config objects
        """
        self.defaults.emit()


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
    Emergency = auto()


class ConfigFixStrategy(IntEnum):
    Ignore = auto()
    Merge = auto()
    MergeAll = auto()
    Defaults = auto()
    DefaultsAll = auto()
    HaltModule = auto()
    Halt = auto()



class Doctor(QObject):
    """
    Medic! This class handles errors and startup modes
    """
    def __init__(self):
        super(Doctor, self).__init__()
        self.startupMode = StartupMode.Normal
        self.file = None
        self.logger = logging.getLogger(__name__)
        self.defaultMergeStrategy = ConfigFixStrategy.MergeAll

        self.broken_config = None
        self.broken_key = None

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

    @pyqtSlot(QObject, str)
    def configKeyError(self, conf, key):
        if conf is None:
            return
        self.logger.critical("KeyError has been handled")
        self.broken_config = conf
        self.broken_key = key
        self.notifyOnError(conf, key)
        if self.executeConfigFix(conf):
            self.logger.critical("Performing emergency shutdown...")
            Classes.MainWindow().close()

    def executeConfigFix(self, conf):
        if conf._fixStrategy == ConfigFixStrategy.Merge:
            self.logger.warning("Merging config files...")
            conf.mergeDefaults()
            return True

        elif conf._fixStrategy == ConfigFixStrategy.MergeAll:
            self.logger.warning("Merging all config files...")
            # Ensure that it is loaded
            conf.mergeDefaults()
            conf.blockSignals(True)
            config_manager.merge.emit()
            conf.blockSignals(False)
            return True

        elif conf._fixStrategy == ConfigFixStrategy.Defaults:
            self.logger.warning("Restoring defaults for the config...")
            conf.loadDefaults()
            return True

        elif conf._fixStrategy == ConfigFixStrategy.DefaultsAll:
            self.logger.warning("Restoring all defaults...")
            conf.loadDefaults()
            conf.blockSignals(True)
            config_manager.defaults.emit()
            conf.blockSignals(False)
            return True

        elif conf._fixStrategy == ConfigFixStrategy.HaltModule:
            # TODO finish this
            return False
        return False
        
    def notifyOnError(self, conf, key):
        if conf._fixStrategy <= ConfigFixStrategy.DefaultsAll:
            # Configs have not been restored yet
            msg = QMessageBox()
            msg.setWindowTitle("Doctor")
            defaults = msg.addButton("Restore defaults", QMessageBox.ButtonRole.AcceptRole)
            defaultsAll = msg.addButton("Restore all defaults", QMessageBox.ButtonRole.DestructiveRole)
            ignore = msg.addButton("Ignore", QMessageBox.ButtonRole.RejectRole)

            if conf.meta_name == "unknown":
                msg.setText("Doctor has reported an error in configuration file")
            else:
                msg.setText("Doctor has reported an error in " + conf.meta_name + " (" + conf.meta_desc + ")")

            err = ""
            if key is not None:
                err += "No such key " + str(key) + ". "
            if conf.config_file is not None:
                err += "File: " + conf.config_file

            msg.setDetailedText(err)
            msg.setInformativeText("Restoring defaults would delete your previous config")
            msg.setModal(True)

            msg.exec()

            if msg.clickedButton() == defaults:
                conf._fixStrategy = ConfigFixStrategy.Defaults
            elif msg.clickedButton() == defaultsAll:
                conf._fixStrategy = ConfigFixStrategy.DefaultsAll
            elif msg.clickedButton() == ignore:
                conf._fixStrategy = ConfigFixStrategy.Ignore
            else:
                self.logger.error("No button has been pressed, perhaps the model failed to open")
                conf._fixStrategy = ConfigFixStrategy.Ignore
            # Display message that asks the user to disable the module that throws errors
            # We ignore any errors caused by this module until the next restart

    def handleConfigError(self, conf, key=None):
        """
        Manage config KeyError. Will attempt to recover the state on-the-fly if possible

        Parameters
        ==========
        conf
            config.Config object that caused an error
        key
            (Optional) The key that is missing from the config
        """

        # files are already merged
        if not self.startupMode == StartupMode.Normal:
            if conf._fixStrategy <= ConfigFixStrategy.MergeAll:
                conf._fixStrategy = ConfigFixStrategy.Defaults

        self.executeConfigFix(conf, key)


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
        self.modified = set()

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

        self.modified_file = os.path.join(Common.Basedir, self.config_dir, "modified.json")
        if os.path.exists(self.modified_file):
            with open(self.modified_file, 'r') as f:
                self.modified = set(json.load(f).get("modified", []))

    def save(self):
        """
        Save the list of modified properties
        """
        with open(self.modified_file, 'w') as f:
            json.dump({"modified": list(self.modified)}, f)

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(DefaultsManager, cls).__new__(cls)
        return cls.instance


class CacheManager(QObject):
    """
    Global class that manages cache access. Not intended to be called from other threads
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


defaults_manager = DefaultsManager()
config_manager = ConfigManager()
app_manager = ApplicationManager()
cache_manager = CacheManager()
doctor = Doctor()

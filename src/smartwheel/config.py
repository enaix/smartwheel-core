import json
import os
import weakref

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from smartwheel import common


class Config(QObject):
    """
    Universal configuration class that supports loading and saving json config files.

    Supports direct access by key (ConfigObject["key"]) and other dict methods.

    It acts like collections.ChainMap: all source dicts are stored while merging (update method), which is used in updating settings on-the-fly.

    If any property is updated, Config emits `updated()` signal.

    Note: assertion does not work directly! Config = some_other_dict cannot be overloaded, use Config.c = some_other_dict instead.
    """

    updated = pyqtSignal()

    def __init__(
        self,
        config_file=None,
        default_config_file=None,
        config_dict=None,
        logger=None,
        ignoreNewVars=True,
        varsWhitelist=[],
        varsBlacklist=[],
        updateFunc=None,
        disableSaving=False,
    ):
        """
        Initialize Config object
        Note: the config file needs to be loaded manually by calling loadConfig()

        Parameters
        ==========
        config_file
            (Optional) Path to the configuration file
        default_config_file
            (Optional) Path to the default configuration file, `defaults/...` dir if not specified
        config_dict
            (Optional) Dict containing initial values. Overwritten if config_file is specified
        logger
            logger.Logger instance (recommended, will print to stdout if not given)
        ignoreNewVars
            (Optional) Drop new variables while saving (in order not to write runtime variables to config)
        varsWhitelist
            (Optional) List of keys that override ignoreNewVars option (all new children variables of any depth will be saved)
        varsBlacklist
            (Optional) List of keys that contain runtime variables, new children variables of any depth are ignored
        updateFunc
            (Optional) Update function to call when settings are updated. Use only if signals are not supported
        disableSaving
            (Optional) Do not save config file automatically. False by default
        """
        super(Config, self).__init__()
        self.config_file = config_file
        self.default_config_file = default_config_file

        if self.default_config_file is None and self.config_file is not None:
            self.default_config_file = self.config_file.replace(
                common.defaults_manager.config_dir,
                common.defaults_manager.defaults_config_dir,
                1,
            )

        # self.c = self.loadConfig()
        self.c = config_dict
        self.logger = logger
        self.ignoreNew = ignoreNewVars
        self.whitelist = varsWhitelist
        self.blacklist = varsBlacklist
        self.updateFunc = updateFunc
        self.disableSaving = disableSaving
        self.links = []  # Storing source dicts to allow updating the variables

        common.config_manager.save.connect(self.saveConfig)
        common.config_manager.updated.connect(self.__updated)
        common.config_manager.batchUpdate.connect(self.__batchUpdate)

    def __fetchkey(self, key):
        """
        Get the updated value from the linked dicts. Do not use directly

        Parameters
        ==========
        key
            Dictionary key
        """
        if len(self.links) == 0:
            return self.c[key]

        for i in range(len(self.links)):
            if self.links[i].get(key) is not None:
                return self.links[i][key]
        return self.c[key]

    def update(self, other, include_only=None):
        """
        Call dict update method while saving the linked dict

        Parameters
        ==========
        other
            Other dict to merge
        include_only
            (Optional) Exclude other keys except whitelisted
        """
        if include_only is None:
            self.c.update(other)
        else:
            for key in include_only:
                if other.get(key) is not None:
                    self.c[key] = other[key]

        self.links.append(other)

    def __getitem__(self, key):
        """
        Access config directly (ConfigObject["key"])

        Parameters
        ==========
        key
            The dictionary key
        """
        return self.__fetchkey(key)

    def __setitem__(self, key, newvalue):
        """
        Write to config directly (ConfigObject["key"] = newvalue)

        Parameters
        ==========
        key
            The dictionary key
        newvalue
            Right-hand side value
        """
        self.c[key] = newvalue

    @pyqtSlot(str)
    def __updated(self, key):
        """
        Call the update signal if the property is updated

        Parameters
        ==========
        key
            Updated key
        """
        if self.get(key) is not None:
            if self.updateFunc is not None:
                self.updateFunc()
            self.updated.emit()

    @pyqtSlot(list)
    def __batchUpdate(self, keys):
        """
        Call the update signal if multiple properties may be updated

        Parameters
        ==========
        keys
            Updated keys
        """
        for key in keys:
            if self.get(key) is not None:
                if self.updateFunc is not None:
                    self.updateFunc()
                self.updated.emit()
                break

    def __len__(self):
        return len(self.c)

    def __hash__(self):
        return hash(self.c)

    def __str__(self):
        return str(self.c)

    def __iter__(self):
        return iter(self.c)

    def keys(self):
        return self.c.keys()

    def values(self):
        return self.c.values()

    def get(self, key, default=None):
        """
        Re-implemented dict.get method that respects the linked source dicts

        Parameters
        ==========
        key
            Dict key
        default
            Value to return if the key is not found
        """
        if len(self.links) == 0:
            return self.c.get(key, default)

        for i in range(len(self.links)):
            if self.links[i].get(key) is not None:
                return self.links[i].get(key)

        return self.c.get(key, default)

    def items(self):
        """
        Call the builtin dictionary items method
        """
        return self.c.items()

    def createConfig(self):
        """
        Create config file and underlying file structure if it does not exist

        Returns True if config has been loaded from defaults
        """
        if self.default_config_file is None:
            return False

        if os.path.exists(self.config_file):
            return False

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        ok, defaults = self.loadConfig(
            immediate=True, override=self.default_config_file
        )
        if not ok:
            return

        self.c = defaults

        with open(self.config_file, "w") as f:
            json.dump(defaults, f, indent=4)

        return True

    def loadConfig(self, immediate=False, override=None):
        """
        Load the config from file, returns True if it is loaded successfully

        Parameters
        ==========
        immediate
            If false (default), the function applies the config and does not return it's copy. True - it returns (bool, dict) without applying it
        override
            (Optional) Override config file path with given one
        """
        if self.config_file is None:
            if immediate:
                return True, self.c
            return True

        config_file = self.config_file
        if override is not None:
            config_file = override

        if not override and not immediate:
            if self.createConfig():
                return True

        try:
            with open(config_file, "r") as f:
                if immediate:
                    return True, json.load(f)
                self.c = json.load(f)
                if common.doctor.startupMode == common.StartupMode.Update:
                    self.mergeDefaults()
                elif common.doctor.startupMode == common.StartupMode.Defaults:
                    self.loadDefaults()
        except BaseException as e:
            if self.logger is not None:
                self.logger.error("Could not load config file:")
                self.logger.error(str(e))
            else:
                print("Could not load config file:")
                print(str(e))

            if immediate:
                return False, None
            return False

        return True

    def listIter(self, new, old, dropNew=True, preserveOld=False):
        """
        Recursively iterate through the list and update old config value iff it is present in config file

        Parameters
        ==========
        new
            New values (saved from the application)
        old
            Old values from the json config file
        dropNew
            (Optional) Drop new variables
        preserveOld
            (Optional) Preserve old variables (update only missing)
        """
        if dropNew and not len(new) == len(old):
            return

        # We need to unset the old list in order to prevent duplications errors
        if not dropNew and len(new) < len(old):
            for i in range(len(new), len(old)):
                del old[i]

        for i in range(len(new)):
            if i < len(old):
                if type(new[i]) == type(old[i]):
                    if type(new[i]) == dict:
                        self.dictIter(new[i], old[i], dropNew, preserveOld)
                    elif type(new[i]) == list:
                        self.listIter(new[i], old[i], dropNew, preserveOld)
                    else:
                        if not preserveOld:
                            old[i] = new[i]
            elif not dropNew:
                old.append(new[i])
            else:
                return

    def dictIter(self, new, old, dropNew=True, preserveOld=False):
        """
        Recursively iterate through the dict and update old config value iff it is present in config file

        Parameters
        ==========
        new
            New values (saved from the application)
        old
            Old values from the json config file
        dropNew
            (Optional) Drop new variables
        preserveOld
            (Optional) Preserve old variables (update only missing)
        """
        for key, val in new.items():
            if old.get(key) is not None and type(val) == type(old[key]):
                drop = dropNew
                if dropNew and key in self.whitelist:
                    drop = False
                elif not dropNew and key in self.blacklist:
                    drop = True

                if type(val) == dict:
                    self.dictIter(new[key], old[key], drop, preserveOld)
                elif type(val) == list:
                    self.listIter(val, old[key], drop, preserveOld)
                else:
                    if not preserveOld:
                        old[key] = val
                    # print(key)
            elif not dropNew:
                old[key] = val

    @pyqtSlot()
    def saveConfig(self):
        """
        Save the config file
        Note: new variables are dropped by default (we need to purge runtime variables)
        """
        if self.config_file is None or self.disableSaving:
            return

        # We need to drop runtime variables, so we need to load the json file again
        ok, old_values = self.loadConfig(immediate=True)

        if not ok:
            if self.logger is not None:
                self.logger.error("Failed to apply config")
            else:
                print("Failed to apply config")

            return

        # recursively iterate over the dictionary
        self.dictIter(self.c, old_values, dropNew=self.ignoreNew)

        with open(self.config_file, "w") as f:
            json.dump(old_values, f, indent=4)

    def mergeDefaults(self):
        """
        Refresh config file with default variables. Is invoked in case of an update or config error
        """
        if self.default_config_file is None or self.config_file is None:
            return

        ok, defaults = self.loadConfig(immediate=True, override=self.default_config_file)

        if not ok:
            if self.logger is not None:
                self.logger.error("Failed to merge defaults")
            else:
                print("Failed to merge defaults")
            return

        # Default refresh strategy
        self.dictIter(defaults, self.c, dropNew=False, preserveOld=True)
        self.dictIter(self.c, defaults, dropNew=self.ignoreNew)

        with open(self.config_file, "w") as f:
            json.dump(defaults, f, indent=4)

    def loadDefaults(self):
        """
        Reload config file from defaults
        """
        if self.default_config_file is None or self.config_file is None:
            return

        ok, defaults = self.loadConfig(immediate=True, override=self.default_config_file)

        if not ok:
            if self.logger is not None:
                self.logger.error("Failed to merge defaults")
            else:
                print("Failed to merge defaults")
            return

        with open(self.config_file, "w") as f:
            json.dump(defaults, f, indent=4)

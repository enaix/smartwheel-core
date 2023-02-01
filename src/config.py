from PyQt5.QtCore import QObject, pyqtSlot
import json
import os
import common


class Config(QObject):
    """
    Universal configuration class that supports loading and saving json config files.
    Supports direct access by key (ConfigObject["key"]) and other dict methods.
    Note: assertion does not work directly! Config = some_other_dict cannot be overloaded, use Config.c = some_other_dict instead.
    """
    def __init__(self, config_file, logger=None, ignoreNewVars=True, varsWhitelist=[], varsBlacklist=[]):
        """
        Initialize Config object
        Note: the config file needs to be loaded manually by calling loadConfig()

        Parameters
        ==========
        config_file
            Path to the configuration file
        logger
            logger.Logger instance (recommended, will print to stdout if not given)
        ignoreNewVars
            (Optional) Drop new variables while saving (in order not to write runtime variables to config)
        varsWhitelist
            (Optional) List of keys that override ignoreNewVars option (all new children variables of any depth will be saved)
        varsBlacklist
            (Optional) List of keys that contain runtime variables, new children variables of any depth are ignored
        """
        super(Config, self).__init__()
        self.config_file = config_file
        #self.c = self.loadConfig()
        self.c = None
        self.logger = logger
        self.ignoreNew = ignoreNewVars
        self.whitelist = varsWhitelist
        self.blacklist = varsBlacklist

        common.config_manager.save.connect(self.saveConfig)

    def __getitem__(self, key):
        """
        Access config directly (ConfigObject["key"])

        Parameters
        ==========
        key
            The dictionary key
        """
        return self.c[key]

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

    def get(self, *args, **kwargs):
        return self.c.get(*args, **kwargs)

    def items(self):
        """
        Call the builtin dictionary items method
        """
        return self.c.items()

    def loadConfig(self, immediate=False):
        """
        Load the config from file, returns True if it is loaded successfully

        Parameters
        ==========
        immediate
            If false (default), the function applies the config and does not return it's copy. True - it returns (bool, dict) without applying it
        """
        try:
            with open(self.config_file, "r") as f:
                if immediate:
                    return True, json.load(f)
                self.c = json.load(f)
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

    def listIter(self, new, old, dropNew=True):
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
        """
        if dropNew and not len(new) == len(old):
            return

        for i in range(len(new)):
            if i < len(old):
                if type(new[i]) == type(old[i]):
                    if type(new[i]) == dict:
                        self.dictIter(new[i], old[i], dropNew)
                    elif type(new[i]) == list:
                        self.listIter(new[i], old[i], dropNew)
                    else:
                        old[i] = new[i]
            elif not dropNew:
                    old.append(new[i])
            else:
                return

    def dictIter(self, new, old, dropNew=True):
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
        """
        for key, val in new.items():
            if old.get(key) is not None and type(val) == type(old[key]):
                if dropNew and key in self.whitelist:
                    dropNew = False
                elif not dropNew and key in self.blacklist:
                    dropNew = True
                
                if type(val) == dict:
                    self.dictIter(new[key], old[key], dropNew)
                elif type(val) == list:
                    self.listIter(val, old[key], dropNew)
                else:
                    old[key] = val
                    #print(key)
            elif not dropNew:
                old[key] = val

    @pyqtSlot()
    def saveConfig(self):
        """
        Save the config file
        Note: new variables are dropped by default (we need to purge runtime variables)
        """
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



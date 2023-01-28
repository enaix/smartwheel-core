from PyQt5.QtCore import QObject, pyqtSlot 
import json
import os


class Config(QObject):
    def __init__(self, config_file):
        super(Config, self).__init__()
        self.config_file = config_file
        self.c = self.loadConfig()

    def __getitem__(self, key):
        return self.c[key]

    def items(self):
        return self.c.items()

    def loadConfig(self):
        with open(self.config_file, "r") as f:
            return json.load(f)

    def listIter(self, new, old):
        if not len(new) == len(old):
            return

        for i in range(len(new)):
            if type(new[i]) == type(old[i]):
                if type(new[i]) == dict:
                    self.dictIter(new[i], old[i])
                elif type(new[i]) == list:
                    self.listIter(new[i], old[i])
                else:
                    old[i] = new[i]

    def dictIter(self, new, old):
        for key, val in new.items():
            if old.get(key) is not None and type(val) == type(old[key]):
                if type(val) == dict:
                    self.dictIter(new[key], old[key])
                elif type(val) == list:
                    self.listIter(val, old[key])
                else:
                    old[key] = val
                    #print(key)

    @pyqtSlot()
    def saveConfig(self):
        # We need to drop runtime variables, so we need to load the json file again
        old_values = self.loadConfig()
        
        # recursively iterate over the dictionary
        self.dictIter(self.c, old_values)

        with open(os.path.join(self.launch_config["config_dir"], "config.json"), "w") as f:
            json.dump(old_values, f, indent=4)



import importlib
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import time
import json
import os
from actionengine import ActionEngine
from serialpipe.serial import SConn
import weakref

class MList(list):
    def __init__(self):
        super().__init__()

class MDict(dict):
    #def __init__(self):
    #    super().__init__()
    pass

class RootCanvas():
    def __init__(self, WConfig, update_func):
        self.conf = WConfig
        self.update_func = update_func
        self.loadCommonConf()
        self.processCommonConfig()
        # TODO add try catch everywhere
        self.loadInternalModules()
        self.startInternalModules()
        self.wheel_modules = self.loadSections(self.conf["wheelModules"])
        self.cur_wheel_modules = self.wheel_modules
        if self.wheel_modules == 1:
            raise KeyError
        self.loadModules()
        self.tick = 0
        self.loadActionEngine()
        self.loadSerial()

    def loadCommonConf(self):
        try:
            with open(self.conf["commonConfig"], 'r') as f:
                self.common_config = json.load(f)
        except BaseException:
            print("Could not find config file", self.conf["commonConfig"])
            os.exit(1)

    def loadModules(self):
        for i in self.conf["modulesLoad"]:
            self.conf["modules"][i]["class"] = self.importModule(self.conf["modules"][i])

    def importModule(self, meta):
        mod = importlib.import_module(meta["name"])
        ui = mod.UIElem(meta["config"], {**self.conf, **self.common_config}, self.wheel_modules, self.update_func)
        return ui

    def loadSections(self, modules_list, parent_mod=None):
        mods = MList()
        for i in modules_list:
            mod_dict = next((m for m in self.conf["modules"] if m["name"] == i["name"]), None)
            if i["name"] == "ui.folder":
                mod = MDict(i)
                submod = self.loadSections(mod["modules"], mods)
                if submod == 1:
                    return 1
                mod["modules"] = submod
                # mod["parent"] = weakref.ref(mods)
            elif mod_dict is None:
                continue
            else:
                mod = MDict(mod_dict)
            if parent_mod is not None:
                mod["parent"] = weakref.ref(parent_mod)
            #elif mod is None:
            #    print("Error importing module ", mod["name"], ": No such module. Aborting...",sep="")
            #    return 1
            mod_class = self.loadWheelModule(mod)
            if i["name"] == "ui.folder":
                mod_class["class"].wrapper_pointer = weakref.ref(mod_class)
            mods.append(mod_class)
        return mods

    def processCommonConfig(self):
        conf = {}
        if self.common_config["isWheelWidthFixed"]:
            conf["wheelWidth"] = self.common_config["fixedWheelWidth"]
        else:
            conf["wheelWidth"] = self.conf["width"] // 4
        self.common_config = {**self.common_config, **conf}

    def loadWheelModule(self, module):
        mod = importlib.import_module(module["name"])
        if module.get("config", None) is not None:
            ui = mod.UIElem(module["config"], {**self.conf, **self.common_config})
        else:
            ui = mod.UIElem("", module)
        module["class"] = ui
        #self.pixmap = QImage(self.module["class"].icon_path)
        return module

    def reloadWheelModules(self, is_up, caller=None):
        if is_up:
            if caller["parent"] is not None:
                self.cur_wheel_modules = caller["parent"]()
                #return caller["parent"]()
            #return None
        else:
            self.cur_wheel_modules = caller["modules"]
            #return caller["modules"]
        self.conf["modules"][0]["class"].reloadModules(self.cur_wheel_modules)

    def loadInternalModules(self):
        self.conf["internal"] = {}
        for i in range(len(self.conf["internalModules"])):
            mod = self.conf["internalModules"][i]
            mod_class = importlib.import_module(mod["name"]).Internal({**self.conf, **self.common_config}, mod.get("config", None))
            self.conf["internal"][mod_class.name] = {"class": mod_class, "signals": mod_class.getSignals()}

    def startInternalModules(self):
        for i in self.conf["internal"]:
            self.conf["internal"][i]["class"].start()

    def getCurModList(self):
        return self.cur_wheel_modules

    def getWheelModule(self):
        i = self.conf["modules"][0]["class"].getCurModule()
        if i >= len(self.cur_wheel_modules):
            return None
        return self.cur_wheel_modules[i]

    def loadActionEngine(self):
        self.ae = ActionEngine(self.wheel_modules, self.conf["actionEngineConfig"])
        self.ae.current_module_list_getter = self.getCurModList
        self.ae.current_module_getter = self.conf["modules"][0]["class"].getCurModule
        self.ae.canvas = weakref.ref(self)
        self.ae.wheel = weakref.ref(self.conf["modules"][0]["class"])

    def loadSerial(self):
        # TODO move to different module
        # TODO add serial.tools.miniterm in settings
        # TODO add try/except validation
        try:
            self.sc = SConn("config/serial.json", self.ae.callAction)
            self.sc.start()
        except BaseException as e:
            print(e)

    def draw(self, qp):
        #for i in self.conf["modulesLoad"]:
        #    self.conf["modules"][i]["class"].draw(qp)
        self.conf["modules"][0]["class"].draw(qp) # render wheel
        m = self.getWheelModule()
        if self.conf["modules"][0]["class"].is_anim_running or (m is not None and hasattr(m["class"], "is_anim_running") and m["class"].is_anim_running):
            time.sleep(0.01)
            self.update_func()


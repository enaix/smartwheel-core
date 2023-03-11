import importlib
import json
import logging
import os
import queue
import time
import weakref

from PyQt6.QtCore import *
from PyQt6.QtGui import *

import common
import config
import gui_tools
from actionengine import ActionEngine
from tools import merge_dicts


class MList(list):
    """Overloaded list class to store modules. Used to work with weakref"""

    pass


class MDict(dict):
    """Overloaded dict class that represents a module. Uses weakref"""

    pass


class RootCanvas:
    """Main canvas class, manages wheel modules"""

    def __init__(self, WConfig, config_dir, update_func):
        self.common_config = None
        self.config_dir = config_dir
        self.conf = WConfig
        self.update_func = update_func
        self.logger = logging.getLogger(__name__)
        self.loadCommonConf()
        self.processCommonConfig()
        # TODO add try catch everywhere
        self.initCacheDir()
        self.loadInternalModules()
        self.loadBrushes()
        self.startInternalModules()
        self.wheel_modules = self.loadSections(self.conf["wheelModules"])
        self.cur_wheel_modules = self.wheel_modules
        if self.wheel_modules == 1:
            raise KeyError
        self.loadModules()
        self.tick = 0
        self.loadActionEngine()

        self.exec_time = 0.01
        self.exec_window = 0
        self.exec_times = queue.Queue()

    def loadCommonConf(self):
        self.common_config = config.Config(
            os.path.join(self.config_dir, self.conf["commonConfig"]), self.logger
        )
        if not self.common_config.loadConfig():
            self.logger.error("Could not find common config file. Exiting..")
            os.exit(1)

        self.updateIconCache()

    def loadModules(self):
        """
        Read module classes from `modules` config
        """
        for i in self.conf["modulesLoad"]:
            self.conf["modules"][i]["class"] = self.importModule(
                self.conf["modules"][i]
            )

    def importModule(self, meta):
        """
        Import a single module class

        Parameters
        ==========
        meta
            Configuration of the module
        """
        mod = importlib.import_module(meta["name"])
        ui = mod.UIElem(
            os.path.join(self.config_dir, meta["config"]),
            self.conf,
            self.wheel_modules,
            self.update_func,
            weakref.ref(self),
        )
        return ui

    def loadSections(self, modules_list, parent_mod=None):
        """
        Configure already loaded modules or recursively load them in folders

        Parameters
        ==========
        modules_list
            `wheelModules` option from config
        parent_mod
            Folder module (None if it's a root)
        """
        mods = MList()
        for i in modules_list:
            mod_dict = next(
                (m for m in self.conf["modules"] if m["name"] == i["name"]), None
            )
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
            # elif mod is None:
            #    print("Error importing module ", mod["name"], ": No such module. Aborting...",sep="")
            #    return 1
            mod_class = self.loadWheelModule(mod)
            if i["name"] == "ui.folder":
                mod_class["class"].wrapper_pointer = weakref.ref(mod_class)
            mods.append(mod_class)
        return mods

    def initCacheDir(self):
        common.cache_manager.initManager(self.conf)

    def loadBrushes(self):
        b_config = os.path.join(self.conf["brushes_dir"], "config.json")
        if not os.path.exists(b_config):
            self.logger.error("Missing " + b_config + " file")
            os._exit(1)

        with open(b_config, "r") as f:
            self.brushes_conf = json.load(f)

        self.brushes = {}
        self.conf["brush_configs"] = {}

        for mod_name in self.brushes_conf["brushes_modules"]:
            brush = importlib.import_module(self.conf["brushes_dir"] + "." + mod_name)
            b_dict = brush.brushes
            for k in b_dict:
                if self.brushes.get(k) is not None:
                    self.logger.warning("Brush " + k + " is defined twice. Overriding")

                self.conf["brush_configs"][k] = config.Config(
                    os.path.join(
                        self.conf["brushes_dir"],
                        self.brushes_conf["brushes_config_dir"],
                        self.brushes_conf["brushes_config"][k],
                    )
                )
                self.conf["brush_configs"][k].loadConfig()

                self.brushes[k] = b_dict[k](
                    weakref.ref(self.conf), self.conf["brush_configs"][k], weakref.ref(self)
                )

        self.conf["brushesTypes"] = list(self.brushes.keys())

    def processCommonConfig(self):
        """
        Add some properties to the common config and merge it with self.conf
        """
        if self.common_config["isWheelWidthFixed"]:
            self.common_config["wheelWidth"] = self.common_config["fixedWheelWidth"]
        else:
            self.common_config["wheelWidth"] = self.conf["width"] // 4
        self.common_config["configDir"] = self.config_dir

        # Merging configs in order to make settings editable on-the-fly
        merge_dicts(self.conf, self.common_config)

    def loadWheelModule(self, module):
        mod = importlib.import_module(module["name"])
        if module.get("config", None) is not None:
            ui = mod.UIElem(os.path.join(self.config_dir, module["config"]), self.conf)
        else:
            ui = mod.UIElem("", module)
        module["class"] = ui
        # self.pixmap = QImage(self.module["class"].icon_path)
        return module

    def reloadWheelModules(self, is_up, caller=None):
        if is_up:
            if caller["parent"] is not None:
                self.cur_wheel_modules = caller["parent"]()
                # return caller["parent"]()
            # return None
        else:
            self.cur_wheel_modules = caller["modules"]
            # return caller["modules"]
        self.conf["modules"][0]["class"].reloadModules(self.cur_wheel_modules)

    def loadInternalModules(self):
        self.conf["internal"] = {}
        for i in self.conf["internalModulesLoad"]:
            mod = self.conf["internalModules"][i]
            if mod.get("config") is not None:
                cnf = os.path.join(self.config_dir, mod["config"])
            else:
                cnf = None
            mod_class = importlib.import_module(mod["name"]).Internal(self.conf, cnf)
            self.conf["internal"][mod_class.name] = {
                "class": mod_class,
                "signals": mod_class.getSignals(),
            }

    def startInternalModules(self):
        for i in self.conf["internal"]:
            self.conf["internal"][i]["class"].start()

    def getCurModList(self):
        """
        Get current wheel modules
        """
        return self.cur_wheel_modules

    def getWheelModule(self):
        i = self.conf["modules"][0]["class"].getCurModule()
        if i >= len(self.cur_wheel_modules):
            return None
        return self.cur_wheel_modules[i]

    def loadActionEngine(self):
        self.ae = ActionEngine(
            self.wheel_modules,
            os.path.join(self.config_dir, self.conf["actionEngineConfig"]),
            self.conf
        )
        self.ae.current_module_list_getter = self.getCurModList
        self.ae.current_module_getter = self.conf["modules"][0]["class"].getCurModule
        self.ae.canvas = weakref.ref(self)
        self.ae.wheel = weakref.ref(self.conf["modules"][0]["class"])

    def updateIconCache(self):
        """
        Will only be called if icon color has been changed
        """
        res1 = gui_tools.icon_managers["wheel"].setIconColor(
            self.common_config["wheelIconColor"]
        )
        return (
            gui_tools.icon_managers["sections"].setIconColor(
                self.common_config["sectionsIconColor"]
            )
            or res1
        )

    def calculateSmoothFPS(self, new_time):
        """
        Calculate the average render time out of n frames

        Parameters
        ==========
        new_time
            The most recent frame render time
        """
        if self.exec_window == 0:
            self.exec_times.put(new_time)
            self.exec_time = new_time
            self.exec_window += 1
            return

        if self.exec_window < self.conf["fpsFramesSmooth"]:
            self.exec_window += 1
            self.exec_times.put(new_time)
            self.exec_time = (
                (self.exec_window - 1) * self.exec_time + new_time
            ) / self.exec_window
            return

        last_time = self.exec_times.get()
        self.exec_times.put(new_time)

        self.exec_time = (
            self.exec_window * self.exec_time - last_time + new_time
        ) / self.exec_window

    def draw(self, qp):
        """
        Main draw function

        Parameters
        ----------
        qp
            QPainter object
        """
        # for i in self.conf["modulesLoad"]:
        #    self.conf["modules"][i]["class"].draw(qp)
        self.conf["modules"][0]["class"].draw(qp)  # render wheel
        m = self.getWheelModule()
        if (
            self.conf["modules"][0]["class"].is_anim_running
            or (
                m is not None
                and hasattr(m["class"], "is_anim_running")
                and m["class"].is_anim_running
            )
            or self.updateIconCache()
        ):
            if self.conf["stabilizeFPS"]:
                sleep_time = max(1 / self.conf["fps"] - self.exec_time, 0)
            else:
                sleep_time = 1 / self.conf["fps"]

            time.sleep(sleep_time)

            start_time = time.time()

            self.update_func()  # TODO add another update event

            e_time = (time.time() - start_time) * 1000

            if self.conf["stabilizeFPS"]:
                if self.conf["logFPS"]:
                    self.logger.info(
                        "FPS(AVG): "
                        + str(round(1 / max(sleep_time + self.exec_time, 0.0000001), 1))
                    )
                self.calculateSmoothFPS(e_time)

            else:
                if self.conf["logFPS"]:
                    self.logger.info("FPS: " + str(round(1 / (sleep_time + e_time), 1)))

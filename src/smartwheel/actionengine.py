import importlib
import logging
import os
import weakref

from PyQt6.QtCore import *

from smartwheel import config, tools


class ActionEngine(QObject):
    """Modules and wheel interactions interface"""

    callAction = pyqtSignal(tuple, name="action_call")

    def __init__(self, modules, config_file, WConfig):
        """
        Initialize ActionEngine

        Parameters
        ----------
        modules
            Wheel modules
        config_file
            Configuration file (actionengine.json)
        WConfig
            Canvas config
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.importConfig(config_file)
        tools.merge_dicts(self.conf, WConfig)
        self.current_module = 0
        self.current_module_getter = None
        self.current_module_list_getter = None
        self.canvas = None
        self.wheel = None
        self.modules = modules
        self.callAction.connect(self.processCall)
        self.actions = {}
        self.importActions()
        self.importWheelActions()

    def importConfig(self, config_file):
        """
        Load config file (actionengine.json)

        Parameters
        ----------
        config_file
            Filename

        """
        self.conf = config.Config(
            config_file=config_file, logger=self.logger, varsWhitelist=["commandBind"]
        )
        self.conf.loadConfig()

    def importActions(self):
        """
        Import actions from `actions` folder
        """
        for mod in self.conf["actionModulesLoad"]:
            name = self.conf["actionModules"][mod]["name"]
            self.actions[name.split(".")[-1:][0]] = importlib.import_module(
                "smartwheel." + name
            ).Action()

    def importWheelActions(self):
        """
        Import actions from `actions/wheel` folder
        """
        self.wheel_actions = {}
        for mod in self.conf["wheelActionModulesLoad"]:
            mod_class = importlib.import_module(
                "smartwheel." + self.conf["wheelActionModules"][mod]["name"]
            ).WheelAction()
            self.wheel_actions[mod_class.type] = mod_class

    def getModule(self, i):
        """
        Get i-th module

        Parameters
        ----------
        i
            Index of module
        """
        if i >= len(self.modules):
            return None
        return self.modules[i]

    def action(self, call):
        """
        Execute action

        Parameters
        ----------
        call
            Module action (from actions list)
        """
        self.modules = self.current_module_list_getter()
        self.current_module = self.current_module_getter()
        if self.getModule(self.current_module) == None:
            return
        context = (
            self.modules[self.current_module]["class"].conf["actions"].get(call, None)
        )
        if context is None:
            return
        for i in context:
            i["canvas"] = self.canvas
            i["wheel"] = self.wheel
            i["module"] = weakref.ref(self.modules[self.current_module]["class"])
            i["call"] = call
            self.actions[i["action"].lower()].run(i)

    def getWheelAction(self, a):
        """
        Find wheel action
        a
           TODO understand this
        """
        for i in self.conf["commandActions"]:
            if i["type"] == a["mode"] and i["name"] == a["action"]:
                return i
        return None

    def getState(self):
        """
        Get current state (sections opened or closed)
        """
        if self.canvas().conf["modules"][0]["class"].is_sections_hidden:
            return "module"
        return "wheel"

    @pyqtSlot(tuple)
    def processCall(self, p_call):
        """
        Execute action by call (slot function)
        This is the main interface of ActionEngine, check serial.py for example

        Parameters
        ----------
        p_call
            callAction in the form of (bind, command)
            bind is a dict that contains 'name' string
            command is a dict with 'string' field (the command)
        """
        elem, call = p_call
        cur_state = self.getState()

        if elem.get("name") is None or call.get("string") is None:
            self.logger.warning("actionengine could not parse the signal")

        self.logger.debug("Incoming call: " + call["string"])

        i = self.conf["commandBind"].get(elem["name"], None)
        if i is not None:
            c = list(j for j in i if j["command"] == call["string"])
            if c:  # c != []
                for act in c:
                    for a in act["actions"]:
                        cmd = self.getWheelAction(a)
                        if cmd is not None:
                            onState = a.get("onState", None)
                            if onState is not None:
                                if a.get("checkState", True) and onState != cur_state:
                                    continue
                            elif a.get("checkState", True) and a["mode"] != cur_state:
                                continue
                            for _ in range(1 + a.get("repeat", 0)):
                                self.wheel_actions[cmd["type"]].run(
                                    cmd["name"], self.canvas, weakref.ref(self)
                                )
                self.canvas().update_func()
        else:
            self.logger.warning("actionengine could not find call with this name")

    def loadModulesConf(self, conf):
        self.modules.append(conf)

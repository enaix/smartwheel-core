from PyQt5.QtCore import *
import json
import os
import importlib
import weakref


class ActionEngine(QObject):
    """Modules and wheel interactions interface"""
    callAction = pyqtSignal(tuple)

    def __init__(self, modules, config_file):
        """
        Initialize ActionEngine

        Parameters
        ----------
        modules
            Wheel modules
        config_file
            Configuration file (actionengine.json)
        """
        super().__init__()
        self.importConfig(config_file)
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
        with open(config_file, "r") as f:
            self.conf = json.load(f)

    def importActions(self):
        """
        Import actions from `actions` folder
        """
        for mod in os.listdir("actions"):
            if mod == "__init__.py" or mod[-3:] != '.py' or mod == "baseaction.py":
                continue
            self.actions[mod[:-3]] = importlib.import_module("actions." + mod[:-3]).Action()

    def importWheelActions(self):
        """
        Import actions from `actions/wheel` folder
        """
        self.wheel_actions = {}
        for mod in os.listdir(os.path.join("actions", "wheel")):
            if mod == "__init__.py" or mod[-3:] != '.py' or mod == "base.py":
                continue
            mod_class = importlib.import_module("actions.wheel." + mod[:-3]).WheelAction()
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
        context = self.modules[self.current_module]["class"].conf["actions"].get(call, None)
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
        """
        elem, call = p_call
        cur_state = self.getState()
        i = self.conf["commandBind"].get(elem["name"], None)
        if i is not None:
            c = list(j for j in i if j["command"] == call["string"])
            if c != []:
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
                                self.wheel_actions[cmd["type"]].run(cmd["name"], self.canvas, weakref.ref(self))
                self.canvas().update_func()

    def loadModulesConf(self, conf):
        self.modules.append(conf)

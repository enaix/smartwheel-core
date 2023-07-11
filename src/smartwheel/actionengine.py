import importlib
import logging
import os
import weakref

from PyQt6.QtCore import *

from smartwheel import config, tools
from smartwheel.api.action import Pulse, DevicePulse, PulseTypes


class ActionEngine(QObject):
    """Modules and wheel interactions interface"""

    callAction = pyqtSignal(DevicePulse, name="action_call")

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

    def action(self, call: str, pulse: Pulse = None):
        """
        Execute action

        Parameters
        ----------
        call
            Module action (from actions list)
        pulse
            Emitted pulse, may be None
        """
        if pulse is None:
            pulse = Pulse(pulse_type=PulseTypes.BUTTON)

        self.modules = self.current_module_list_getter()
        self.current_module = self.current_module_getter()
        if self.getModule(self.current_module) is None:
            return

        if self.modules[self.current_module]["class"].conf.get("actions") is None:
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
            self.actions[i["action"].lower()].run(i, pulse)

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

    @pyqtSlot(DevicePulse)
    def processCall(self, p_call):
        """
        Execute action by call (slot function)
        This is the main interface of ActionEngine, check serial.py for example

        Parameters
        ----------
        p_call
            DevicePulse class that contains several fields
            bind: string that contains action bind/device name (in actionengine config)
            command: string that contains device command
            type: either PulseTypes.BUTTON or PulseTypes.ENCODER
        """
        elem = p_call.bind
        call = p_call.command

        cur_state = self.getState()

        if elem is None or call is None:
            self.logger.warning("actionengine could not parse the signal")

        self.logger.debug("Incoming call: " + call)

        pulse = self.generatePulse(p_call)

        i = self.conf["commandBind"].get(elem, None)
        if i is not None:
            c = list(j for j in i if j["command"] == call)
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
                                    cmd["name"], pulse
                                )
                self.canvas().update_func()
        else:
            self.logger.warning("actionengine could not find call with this name")

    def generatePulse(self, dpulse: DevicePulse):
        """
        Process device pulse and return new Pulse object

        Parameters
        ==========
        dpulse
            Emitted device pulse
        """
        pulse = Pulse()
        pulse.type = dpulse.type

        if pulse.type == PulseTypes.BUTTON:
            return pulse

        # TODO add actual pulses processing

        pulse.click = True
        pulse.step = 0.0
        pulse.target = 0.0
        pulse.velocity = 0.0

        return pulse

    def loadModulesConf(self, conf):
        self.modules.append(conf)

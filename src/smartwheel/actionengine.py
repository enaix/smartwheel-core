import importlib
import logging
import os
import weakref

from PyQt6.QtCore import *

from smartwheel import config, tools
from smartwheel.api.action import Pulse, DevicePulse, PulseTypes


class AccelerationMeta:
    """
    Internal acceleration metadata for each pulse
    """
    def __init__(self, step, target, velocity, accel, maxvel, n_positions=10):
        self.step = step
        self.target = target
        self.velocity = velocity
        self.acceleration = accel
        self.maxVelocity = maxvel

        # TODO add n_positions fetch and move angles to ActionEngine
        self.angles = [x for x in range(0, 360, 360//n_positions)]

    step: float = None

    target: float = None

    velocity: float = None

    acceleration: float = None

    maxVelocity: float = None

    threshClick: bool = False


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

        self.accelMeta = {}
        self.accelTime = QTimer(self)
        self.accelTime.setInterval(self.conf["acceleration"]["pulseRefreshTime"])
        self.accelTime.timeout.connect(self.pulseCycle)

    def importConfig(self, config_file):
        """
        Load config file (actionengine.json)

        Parameters
        ----------
        config_file
            Filename

        """
        self.conf = config.Config(
            config_file=config_file, logger=self.logger, varsWhitelist=["commandBind", "acceleration"]
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
    def processCall(self, p_call: DevicePulse):
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

    @pyqtSlot()
    def oldPulseCycle(self):
        """
        Generate intermediate pulses using fancy physics formulas
        """
        for key, _ in self.accelMeta.items():
            if self.accelMeta[key].step == self.accelMeta[key].target and self.accelMeta[key].acceleration == 0.0:
                continue

            pulse = key
            pulse._virtual = True

            # Calculate current steps from gravity
            # steps: [-1.0, 1.0]

            # gravity_func = lambda x:

            gravity = (-self.accelMeta[key].step) * self.conf["acceleration"]["gravity"] / self.conf["acceleration"]["pulseRefreshTime"]
            stopped = False

            #  *---.----*
            #  at 0.0: gravity = 0
            #  at 
            #  at 1.0: gravity = -1.0
            #  at -1.0: gravity = 1.0

            self.accelMeta[key].acceleration -= gravity
            self.accelMeta[key].threshClick = False

            # Subtract gravity steps from
            # if 0.0 <= self.accelMeta[key].step < self.conf["acceleration"]["switchThreshold"]:
            #     # less than thresh, > 0
            #     self.accelMeta[key].acceleration -= gravity
            #     self.accelMeta[key].threshClick = False
            # elif 0.0 >= self.accelMeta[key].step > 1.0 - self.conf["acceleration"]["switchThreshold"]:
            #     # less than thresh, < 0
            #     self.accelMeta[key].acceleration += gravity
            #     self.accelMeta[key].threshClick = False
            if abs(self.accelMeta[key].step) >= self.conf["acceleration"]["switchThreshold"]:
                # more than thresh
                if not self.accelMeta[key].threshClick:
                    pulse._click = True
                self.accelMeta[key].threshClick = True

                if abs(self.accelMeta[key].acceleration) < self.conf["acceleration"]["maxStopAccel"]:
                    self.accelMeta[key].step = 0.0
                    self.accelMeta[key].target = 0.0
                    self.accelMeta[key].acceleration = 0.0
                    stopped = True

                if self.accelMeta[key].step > 0:
                    # > 0
                    self.accelMeta[key].acceleration += gravity
                else:
                    # < 0
                    self.accelMeta[key].acceleration -= gravity

            if not stopped:
                self.accelMeta[key].step += self.accelMeta[key].acceleration / self.conf["acceleration"]["pulseRefreshTime"]

            if abs(self.accelMeta[key].step) >= 1.0:
                if self.accelMeta[key].step > 0:
                    # >= 1.0
                    self.accelMeta[key].step -= 1.0
                    self.accelMeta[key].target = \
                        0.0 if self.accelMeta[key].step < self.conf["acceleration"]["switchThreshold"] else 1.0
                else:
                    # <= -1.0
                    self.accelMeta[key].step += 1.0
                    self.accelMeta[key].target = \
                        0.0 if self.accelMeta[key].step > 1.0 - self.conf["acceleration"]["switchThreshold"] else -1.0

            if abs(self.accelMeta[key].target - self.accelMeta[key].step) < self.conf["acceleration"]["deadzone"] and \
                    abs(self.accelMeta[key].acceleration) < self.conf["acceleration"]["minAccel"]:
                self.accelMeta[key].step = 0.0
                self.accelMeta[key].target = 0.0
                self.accelMeta[key].acceleration = 0.0
                # we should not stop the timer as there may be >1 encoder
                # self.accelTime.stop()

            self.logger.debug("Step: " + str(self.accelMeta[key].step) + "; target: " + str(self.accelMeta[key].target)
                              + "; vel: " + str(self.accelMeta[key].acceleration))

            self.callAction.emit(pulse)

    @pyqtSlot()
    def pulseCycle(self):
        for key, _ in self.accelMeta.items():
            pulse = key
            pulse._virtual = True

            # TODO add O(1) nearest angle calculation
            nearest_angle = min(self.accelMeta[key].angles, key=lambda x: abs(x - self.accelMeta[key].step))

            # calculate the direction towards the nearest fixed angle
            direction = 1 if nearest_angle > self.accelMeta[key].step else -1

            # update the position with inertia
            self.accelMeta[key].step += self.accelMeta[key].acceleration * self.conf["acceleration"]["pulseRefreshTime"] / 1000

            if not self.accelMeta[key].target == nearest_angle:
                pulse._click = True
                self.accelMeta[key].target = nearest_angle

            if False and abs(nearest_angle - self.accelMeta[key].step) < self.conf["acceleration"]["deadzone"] and\
                    abs(self.accelMeta[key].acceleration) < self.conf["acceleration"]["maxStopAccel"]:
                self.accelMeta[key].acceleration = 0
                self.accelMeta[key].step = nearest_angle
            else:
                # constantly adjust inertia based on the current direction
                self.accelMeta[key].acceleration += self.conf["acceleration"]["gravity"] * direction

            self.callAction.emit(pulse)
            self.logger.debug("Step: " + str(self.accelMeta[key].step) + "; target: " + str(nearest_angle)
                              + "; vel: " + str(self.accelMeta[key].acceleration))


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

        if dpulse._virtual:
            pulse.virtual = True
            if dpulse._click:
                pulse.click = True
            pulse.step = self.accelMeta[dpulse].step
            pulse.target = self.accelMeta[dpulse].target
            pulse.velocity = self.accelMeta[dpulse].acceleration
            return pulse

        if pulse.type == PulseTypes.BUTTON:
            return pulse

        if dpulse.up is None:
            self.logger.error("Device encoder pulse direction is unset")
            pulse.click = False
            pulse.step = 0.0
            pulse.target = 0.0
            pulse.velocity = 0.0
            pulse.virtual = False
            return pulse

        if self.accelMeta.get(dpulse) is None:
            if dpulse.up:
                accel = self.conf["acceleration"]["clickAccel"]
            else:
                accel = -self.conf["acceleration"]["clickAccel"]

            self.accelMeta[dpulse] = AccelerationMeta(0.0, 0.0, 0.0, accel,
                                                      self.conf["acceleration"]["maxAccel"])
        else:
            if dpulse.up:
                self.accelMeta[dpulse].acceleration += self.conf["acceleration"]["clickAccel"]
            else:
                self.accelMeta[dpulse].acceleration -= self.conf["acceleration"]["clickAccel"]

            if abs(self.accelMeta[dpulse].acceleration) >= self.conf["acceleration"]["maxAccel"]:
                if self.accelMeta[dpulse].acceleration > 0:
                    self.accelMeta[dpulse].acceleration = self.conf["acceleration"]["maxAccel"]
                else:
                    self.accelMeta[dpulse].acceleration = -self.conf["acceleration"]["maxAccel"]

        pulse.virtual = False
        pulse.click = False
        pulse.step = self.accelMeta[dpulse].step
        pulse.target = self.accelMeta[dpulse].target
        pulse.velocity = self.accelMeta[dpulse].acceleration

        if not self.accelTime.isActive():
            self.accelTime.start()

        return pulse

    def loadModulesConf(self, conf):
        self.modules.append(conf)

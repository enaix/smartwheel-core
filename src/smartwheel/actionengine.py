import importlib
import logging
import os
import weakref

from PyQt6.QtCore import *

from smartwheel import config, tools
from smartwheel.api.app import Classes
from smartwheel.api.action import Pulse, DevicePulse, PulseTypes


class AccelerationMeta:
    """
    Internal acceleration metadata for each pulse
    """

    def __init__(self, step, target, velocity, accel, maxvel):
        self.step = step
        self.target = target
        self.velocity = velocity
        self.acceleration = accel
        self.maxVelocity = maxvel

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
        super(ActionEngine, self).__init__()
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

        self.last_state = True  # wheel
        self.angles = [0.0, 0.0]  # angles for wheel and module states
        self.positions_list = [Classes.RootCanvas().common_config["selectionWheelEntries"],
                               self.conf["acceleration"]["moduleSections"]]
        self.n_positions = self.positions_list[0]  # Current number of sections
        self.accelMeta = {}
        self.devicePulses = {}
        self.accelTime = QTimer(self)
        self.accelTime.setInterval(self.conf["acceleration"]["pulseRefreshTime"])
        self.accelTime.timeout.connect(self.pulseCycle)

        # Initialize debugging parameters
        self.conf["debug"] = {}
        self.conf["debugPulses"] = []
        self.conf["debugLookupKey"] = ""

    def importConfig(self, config_file):
        """
        Load config file (actionengine.json)

        Parameters
        ----------
        config_file
            Filename

        """
        self.conf = config.Config(
            config_file=config_file, logger=self.logger, varsWhitelist=["commandBind", "acceleration", "logEngine", "debugLookupKey"]
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
        if Classes.RootCanvas().conf["modules"][0]["class"].is_sections_hidden:
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

        if not p_call._virtual:
            # All pulses are blocked while the sections are being opened/closed
            if Classes.RootCanvas().conf["modules"][0]["class"].is_sections_anim_running:
                return

            self.logger.debug("Incoming call: " + elem + "." + call)

        pulse = self.generatePulse(p_call, cur_state == "wheel")

        # TODO rewrite this in constant time
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
                Classes.RootCanvas().update_func()
        else:
            self.logger.warning("actionengine could not find call with this name")

    @staticmethod
    def sign(x):
        return -1.0 if x < 0.0 else 1.0

    @pyqtSlot()
    def pulseCycle(self, singleShot=False):
        self.conf["debug"] = {}

        for key, _ in self.accelMeta.items():
            pulse = key.copy()
            pulse._virtual = True
            pulse._click = False

            # Not spinning
            if singleShot and \
                    self.accelMeta[key].target == self.accelMeta[key].step and self.accelMeta[key].acceleration == 0.0:
                self.callAction.emit(pulse)
                return

            # calculate nearest angle among the sections (360 / n_positions)
            nearest_angle = self.accelMeta[key].target
            # upper bound
            if abs(self.accelMeta[key].target + 360.0 / self.n_positions - self.accelMeta[key].step) < \
                    abs(self.accelMeta[key].target - self.accelMeta[key].step):
                nearest_angle = self.accelMeta[key].target + 360.0 / self.n_positions

            # lower bound
            elif abs(self.accelMeta[key].target - 360.0 / self.n_positions - self.accelMeta[key].step) < \
                    abs(self.accelMeta[key].target - self.accelMeta[key].step):
                nearest_angle = self.accelMeta[key].target - 360.0 / self.n_positions

            # calculate the direction towards the nearest fixed angle
            direction = 1 if nearest_angle > self.accelMeta[key].step else -1

            # calculate the normalized distance to the nearest angle
            norm_dist = abs(self.accelMeta[key].step - nearest_angle) / (180.0 / self.n_positions)

            # calculate deltaTime
            delta = self.conf["acceleration"]["pulseRefreshTime"] / 1000

            # update the position with inertia
            self.accelMeta[key].step += self.accelMeta[key].acceleration * delta

            # change of direction
            if not self.accelMeta[key].target == nearest_angle:
                pulse._click = True
                # check the direction
                if self.accelMeta[key].target > nearest_angle:
                    pulse.up = False
                else:
                    pulse.up = True

                self.accelMeta[key].target = nearest_angle

            old_accel = self.accelMeta[key].acceleration

            # friction calculation
            self.accelMeta[key].acceleration += (-self.accelMeta[key].acceleration) * ((1.0 - norm_dist) ** 2) * \
                                                 self.conf["acceleration"]["friction"] * delta

            # constantly adjust inertia based on the current direction
            self.accelMeta[key].acceleration += self.conf["acceleration"]["gravity"] * direction * (
                    0.5 + 0.5 * (1.0 - norm_dist)) * delta

            # change of velocity
            dir_change = self.accelMeta[key].acceleration * old_accel < 0

            stopped = False
            if dir_change and abs(nearest_angle - self.accelMeta[key].step) < self.conf["acceleration"]["deadzone"] and \
                    abs(self.accelMeta[key].acceleration) < self.conf["acceleration"]["maxStopAccel"]:
                self.accelMeta[key].acceleration = 0.0
                self.accelMeta[key].step = nearest_angle
                self.accelTime.stop()
                stopped = True

            # All variables theoretically should be in 0.0 - 360.0 range, but this should be done in modules
            # to cover the edge cases (359.9 -> 0.0). In practice it would take insane amount of spins for the sin
            # and cos functions to break due to precision errors

            if self.conf["debugLookupKey"] == str(key):
                self.conf["debug"] = {"step": self.accelMeta[key].step, "target": self.accelMeta[key].target,
                                      "velocity": self.accelMeta[key].velocity, "distance": norm_dist, "stop": stopped}

            self.callAction.emit(pulse)
            if self.conf["logEngine"]:
                self.logger.debug("Step: " + str(self.accelMeta[key].step) + "; target: " + str(nearest_angle)
                                  + "; vel: " + str(self.accelMeta[key].acceleration) + "; dist: " + str(norm_dist))

    def resetPulse(self, dpulse: DevicePulse, is_wheel_mode: bool):
        """
        Reset pulse to its previous values, sets acceleration to 0

        Parameters
        ==========
        dpulse
            DevicePulse to reset
        is_wheel_mode
            Application state, either wheel (True) or module
        """
        self.accelMeta[dpulse].velocity = 0.0
        self.accelMeta[dpulse].acceleration = 0.0

        # Right now the angle is saved for the modules globally. Perhaps it should be changed...
        self.angles[int(not is_wheel_mode)] = self.accelMeta[dpulse].target  # save current angle

        # reset current angle
        self.accelMeta[dpulse].step = self.angles[int(is_wheel_mode)]
        self.accelMeta[dpulse].target = self.accelMeta[dpulse].step

        # update number of positions
        self.n_positions = self.positions_list[int(not is_wheel_mode)]

    def angleChanged(self, up=True):
        """
        Increment/decrement the angle (wheel)

        Parameters
        ==========
        up
            Increment up (if True)
        """
        self.angles[0] += (1 if up else -1) * 360.0 / self.n_positions

    def wheelStateChanged(self, is_wheel_mode: bool):
        """
        Update all device pulses on wheel state change

        Parameters
        ==========
        is_wheel_mode
            Application state, either wheel (True) or module
        """
        for key, _ in self.devicePulses.items():
            self.resetPulse(self.devicePulses[key], is_wheel_mode)

        # execute force update
        self.pulseCycle(True)

    def generatePulse(self, dpulse: DevicePulse, is_wheel_mode: bool):
        """
        Process device pulse and return new Pulse object

        Parameters
        ==========
        dpulse
            Emitted device pulse
        is_wheel_mode
            Application state, either wheel (True) or module
        """
        pulse = Pulse()
        pulse.type = dpulse.type

        if dpulse._virtual:
            pulse.virtual = True
            pulse.click = dpulse._click
            if dpulse.up is not None:
                pulse.up = dpulse.up

            pulse.step = self.accelMeta[dpulse].step
            pulse.target = self.accelMeta[dpulse].target
            pulse.velocity = self.accelMeta[dpulse].acceleration

            #if not is_wheel_mode == self.last_state:
            #    self.resetPulse(dpulse, is_wheel_mode)
            #    self.last_state = is_wheel_mode

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

        # Rotary
        if self.accelMeta.get(dpulse) is None:

            # Store DevicePulse instance by its name (__str__ returns device bind)
            self.devicePulses[str(dpulse)] = dpulse
            self.conf["debugPulses"] = [str(x) for x, _ in self.devicePulses.items()]

            if dpulse.up:
                accel = self.conf["acceleration"]["clickAccel"]
            else:
                accel = -self.conf["acceleration"]["clickAccel"]

            self.accelMeta[dpulse] = AccelerationMeta(0.0, 0.0, 0.0, accel,
                                                      self.conf["acceleration"]["maxAccel"])
        else:
            # Update pulse parameters (dpulse as a key does not represent all unique parameters)
            self.devicePulses[str(dpulse)].command = dpulse.command

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
        pulse.up = dpulse.up

        if not self.accelTime.isActive():
            self.accelTime.start()

        return pulse

    def loadModulesConf(self, conf):
        self.modules.append(conf)

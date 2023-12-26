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

    def __init__(self, config_file, WConfig):
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
        self.callAction.connect(self.processCall)
        self.actions = {}
        self.importActions()
        self.importWheelActions()

        self.n_positions = Classes.RootCanvas().common_config["selectionWheelEntries"]  # Current number of sections
        self.haptics = config.Config(logger=self.logger, ignoreNewVars=False, config_dict={}, disableSaving=True)
        self.haptics.updated.connect(self.onHapticsUpdate)
        self.updateModuleHaptics(True)
        self.last_state = True  # wheel
        self.linear_mode_enabled = False
        self.angles = [0.0, 0.0]  # angles for wheel and module states
        self.accelMeta = {}
        self.devicePulses = {}

        self.modules_bind = {}
        self.loadModulesNames()

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
        # TODO (long) add multiple encoders settings
        self.conf = config.Config(
            config_file=config_file, logger=self.logger,
            varsWhitelist=["commandBind", "acceleration", "logEngine", "debugLookupKey"]
        )
        self.conf.loadConfig()
        self.conf.updated.connect(self.updateHapticsConf)

    def loadModulesNames(self):
        """
        Register modules names bind (for settings)
        """
        modules = Classes.RootCanvas().cur_wheel_modules
        self.conf["modulesList"] = []
        self.conf["modulesListPicker"] = ""
        self.conf["moduleNamesList"] = []
        for i in range(len(modules)):
            if modules[i].get("title") is not None:
                self.modules_bind[modules[i]["title"]] = i
                self.conf["modulesList"].append(modules[i]["title"])
            else:
                self.modules_bind[modules[i]["name"]] = i
                self.conf["modulesList"].append(modules[i]["name"])

            self.conf["moduleNamesList"].append(modules[i]["name"])

    def importActions(self):
        """
        Import actions from `actions` folder
        """
        for mod in self.conf["actionModulesLoad"]:
            name = self.conf["actionModules"][mod]["name"]
            self.actions[name.split(".")[-1]] = importlib.import_module(
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

        modules = Classes.RootCanvas().cur_wheel_modules
        current_module = Classes.WheelUi().getCurModule()
        if current_module >= len(modules) or modules[current_module] is None \
                or modules[current_module].get("class") is None:
            return

        if modules[current_module]["class"].conf.get("actions") is None:
            return

        context = (
            modules[current_module]["class"].conf["actions"].get(call, None)
        )
        if context is None:
            return
        for i in context:
            i["module"] = weakref.ref(modules[current_module]["class"])
            i["call"] = call
            self.actions[i["action"].lower()].run(i, pulse)

    def getWheelAction(self, a):
        """
        Find wheel action
        a
           Action to find
        """
        for i in self.conf["commandActions"]:
            if i["type"] == a["mode"] and i["name"] == a["action"]:
                return i
        return None

    def getState(self):
        """
        Get current state (sections opened or closed)
        """
        if Classes.WheelUi().is_sections_hidden:
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
            # All pulses are blocked while the sections are being opened/closed, or it's in the linear mode
            if Classes.WheelUi().is_sections_anim_running or self.linear_mode_enabled:
                self.conf["debug_input_blocked"] = True
                return
            self.conf["debug_input_blocked"] = False

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

    def physics_process(self, key: DevicePulse, pulse: DevicePulse):
        """
        Calculate angle position using haptics engine

        Parameters
        ==========
        key
            DevicePulse to calculate
        pulse
            Virtual DevicePulse to emit
        """
        # calculate section angle
        section_angle = 360.0 / self.haptics["moduleSections"]

        # calculate nearest angle among the sections (360 / n_positions)
        nearest_angle = self.accelMeta[key].target
        # upper bound
        if abs(self.accelMeta[key].target + section_angle - self.accelMeta[key].step) < \
                abs(self.accelMeta[key].target - self.accelMeta[key].step):
            nearest_angle = self.accelMeta[key].target + section_angle * \
                            max((self.accelMeta[key].step - self.accelMeta[key].target) // section_angle, 1)

        # lower bound
        elif abs(self.accelMeta[key].target - section_angle - self.accelMeta[key].step) < \
                abs(self.accelMeta[key].target - self.accelMeta[key].step):
            nearest_angle = self.accelMeta[key].target - section_angle * \
                            max((self.accelMeta[key].target - self.accelMeta[key].step) // section_angle, 1)

        # calculate the direction towards the nearest fixed angle
        direction = 1 if nearest_angle > self.accelMeta[key].step else -1

        # calculate the normalized distance to the nearest angle
        norm_dist = abs(self.accelMeta[key].step - nearest_angle) / (section_angle / 2.0)

        # calculate deltaTime
        delta = self.haptics["pulseRefreshTime"] / 1000

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
                                            self.haptics["friction"] * delta

        # constantly adjust inertia based on the current direction
        self.accelMeta[key].acceleration += self.haptics["gravity"] * direction * (
                0.5 + 0.5 * (1.0 - norm_dist)) * delta

        # change of velocity
        dir_change = self.accelMeta[key].acceleration * old_accel < 0

        stopped = False
        if dir_change and abs(nearest_angle - self.accelMeta[key].step) < self.haptics["deadzone"] and \
                abs(self.accelMeta[key].acceleration) < self.haptics["maxStopAccel"]:
            self.accelMeta[key].acceleration = 0.0
            self.accelMeta[key].step = nearest_angle
            self.accelTime.stop()
            stopped = True

        return pulse, norm_dist, nearest_angle, stopped

    def linear_process(self, key: DevicePulse, pulse: DevicePulse):
        """
        Calculate angle position using linear function

        Parameters
        ==========
        key
            DevicePulse to calculate
        pulse
            Virtual DevicePulse to emit
        """
        # calculate section angle
        section_angle = 360.0 / self.haptics["moduleSections"]

        # calculate deltaTime
        delta = self.haptics["pulseRefreshTime"] / 1000

        if self.accelMeta[key].step < self.accelMeta[key].target:
            direction = 1.0
            pulse.up = True
        else:
            direction = -1.0
            pulse.up = False

        # increment step
        self.accelMeta[key].step += direction * section_angle * delta / self.haptics["linearClickTime"]

        # check for middle position
        if not self.accelMeta[key].threshClick and \
                abs(self.accelMeta[key].step - self.accelMeta[key].target) < section_angle / 2.0:
            pulse._click = True
            self.accelMeta[key].threshClick = True

        stopped = False
        # check for end position
        if self.accelMeta[key].threshClick and abs(self.accelMeta[key].step - self.accelMeta[key].target) < 0.01:
            self.accelTime.stop()
            stopped = True
            self.accelMeta[key].threshClick = False

            # disable linear mode
            if self.linear_mode_enabled:
                self.linear_mode_enabled = False
        elif not self.accelTime.isActive():
            self.accelTime.start()

        return pulse, stopped

    @pyqtSlot()
    def pulseCycle(self, singleShot=False):
        """
        Calculate virtual pulses using fancy formulas

        Parameters
        ==========
        singleShot
            Emit the pulse once and return
        """
        self.conf["debug"] = {}

        for key, _ in self.accelMeta.items():
            pulse = key.copy()
            pulse._virtual = True
            pulse._click = False

            # Not spinning
            if not self.linear_mode_enabled and singleShot and \
                    self.accelMeta[key].target == self.accelMeta[key].step and self.accelMeta[key].acceleration == 0.0:
                self.callAction.emit(pulse)
                continue

            if self.haptics["enableHaptics"] and not self.linear_mode_enabled:
                # Run haptics engine
                pulse, norm_dist, nearest_angle, stopped = self.physics_process(key, pulse)
            else:
                # Run linear calculation
                pulse, stopped = self.linear_process(key, pulse)
                norm_dist = None
                nearest_angle = None

            # All variables theoretically should be in 0.0 - 360.0 range, but this should be done in modules
            # to cover the edge cases (359.9 -> 0.0). In practice it would take insane amount of spins for the sin
            # and cos functions to break due to precision errors

            if self.conf["debugLookupKey"] == str(key):
                self.conf["debug"] = {"step": self.accelMeta[key].step, "target": self.accelMeta[key].target,
                                      "velocity": self.accelMeta[key].acceleration, "distance": norm_dist, "stop": stopped}

            self.callAction.emit(pulse)
            if self.conf["logEngine"]:
                self.logger.debug("Step: " + str(self.accelMeta[key].step) + "; target: " + str(nearest_angle)
                                  + "; vel: " + str(self.accelMeta[key].acceleration) + "; dist: " + str(norm_dist))

    def resetPulse(self, dpulse: DevicePulse, is_wheel_mode: bool, state_change=True):
        """
        Reset pulse to its previous values, sets acceleration to 0

        Parameters
        ==========
        dpulse
            DevicePulse to reset
        is_wheel_mode
            Application state, either wheel (True) or module
        state_change
            Is the application state changed (wheel opened/closed)
        """
        self.accelMeta[dpulse].velocity = 0.0
        self.accelMeta[dpulse].acceleration = 0.0

        if state_change:
            # Right now the angle is saved for the modules globally. Perhaps it should be changed...
            self.angles[int(not is_wheel_mode)] = self.accelMeta[dpulse].target  # save current angle

            # reset current angle
            self.accelMeta[dpulse].step = self.angles[int(is_wheel_mode)]
            self.accelMeta[dpulse].target = self.accelMeta[dpulse].step
        else:
            self.accelMeta[dpulse].step = self.accelMeta[dpulse].target

    def angleChanged(self, up=True):
        """
        Increment/decrement the angle (wheel)

        Parameters
        ==========
        up
            Increment up (if True)
        """
        is_wheel_mode = self.getState() == "wheel"

        if is_wheel_mode:
            self.linear_mode_enabled = True

            for dp, _ in self.devicePulses.items():
                self.resetPulse(self.devicePulses[dp], is_wheel_mode, state_change=False)
                self.accelMeta[dp].target += (1 if up else -1) * 360.0 / self.n_positions
            self.pulseCycle()
        else:
            # Update the angle for wheel mode
            self.angles[1] += (1 if up else -1) * 360.0 / self.n_positions

        self.updateModuleHaptics(is_wheel_mode)

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

        self.updateModuleHaptics(is_wheel_mode)

        # execute force update
        self.pulseCycle(True)

    def updateModuleHaptics(self, is_wheel_mode: bool):
        """
        Load haptics parameters associated with wheel/current module

        Parameters
        ==========
        is_wheel_mode
            Application state, either wheel (True) or module
        """
        if is_wheel_mode:
            for key, value in self.conf["acceleration"].items():
                self.haptics[key] = value
            self.haptics["clickAccelCoeff"] = 1.0
            self.haptics["moduleSections"] = self.n_positions
        else:
            modules = Classes.RootCanvas().cur_wheel_modules
            current_module = Classes.WheelUi().getCurModule()

            if current_module >= len(modules) or modules[current_module] is None or modules[current_module].get("class")\
                    is None or modules[current_module]["class"].conf.get("haptics") is None:
                # Load default params
                self.updateModuleHaptics(True)
                return

            for key, value in modules[current_module]["class"].conf["haptics"].items():
                if value is None:
                    continue
                self.haptics[key] = value

    @pyqtSlot()
    def onHapticsUpdate(self):
        pass

    @pyqtSlot()
    def updateHapticsConf(self):
        """
        Update haptics config on settings change
        """
        self.updateModuleHaptics(self.getState() == "wheel")

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
            # Clear all DevicePulse instances; TODO clear only conflicting pulses

            # We assume that there is only one existing device right now
            new_meta = None
            for dp, _ in self.devicePulses.items():
                self.resetPulse(self.devicePulses[dp], is_wheel_mode, state_change=False)
                new_meta = self.accelMeta[dp]
            self.devicePulses = {}
            self.accelMeta = {}

            # Store DevicePulse instance by its name (__str__ returns device bind)
            self.devicePulses[str(dpulse)] = dpulse
            self.conf["debugPulses"] = [str(x) for x, _ in self.devicePulses.items()]

            if self.haptics["enableHaptics"]:
                if dpulse.up:
                    accel = self.haptics["clickAccel"] * self.haptics["clickAccelCoeff"]
                else:
                    accel = -self.haptics["clickAccel"] * self.haptics["clickAccelCoeff"]

                if new_meta is not None:
                    self.accelMeta[dpulse] = new_meta
                    self.accelMeta[dpulse].acceleration += accel
                else:
                    self.accelMeta[dpulse] = AccelerationMeta(0.0, 0.0, 0.0, accel, self.haptics["maxAccel"])
            else:
                if new_meta is not None:
                    self.accelMeta[dpulse] = new_meta
                    self.accelMeta[dpulse].target += (1 if dpulse.up else -1) * 360.0 / self.n_positions
                else:
                    target = (1 if dpulse.up else -1) * 360.0 / self.n_positions
                    self.accelMeta[dpulse] = AccelerationMeta(0.0, target, 0.0, 0.0, self.haptics["maxAccel"])

        else:
            # Update pulse parameters (dpulse as a key does not represent all unique parameters)
            self.devicePulses[str(dpulse)].command = dpulse.command

            if self.haptics["enableHaptics"]:
                if dpulse.up:
                    self.accelMeta[dpulse].acceleration += self.haptics["clickAccel"] * self.haptics["clickAccelCoeff"]
                else:
                    self.accelMeta[dpulse].acceleration -= self.haptics["clickAccel"] * self.haptics["clickAccelCoeff"]
            else:
                self.accelMeta[dpulse].target += (1 if dpulse.up else -1) * 360.0 / self.n_positions

            if abs(self.accelMeta[dpulse].acceleration) >= self.haptics["maxAccel"]:
                if self.accelMeta[dpulse].acceleration > 0:
                    self.accelMeta[dpulse].acceleration = self.haptics["maxAccel"]
                else:
                    self.accelMeta[dpulse].acceleration = -self.haptics["maxAccel"]

        pulse.virtual = False
        pulse.click = False
        pulse.step = self.accelMeta[dpulse].step
        pulse.target = self.accelMeta[dpulse].target
        pulse.velocity = self.accelMeta[dpulse].acceleration
        pulse.up = dpulse.up

        if not self.accelTime.isActive():
            self.accelTime.start()

        return pulse

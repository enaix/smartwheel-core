from smartwheel.actions.wheel.base import BaseWheelAction

from smartwheel.api.app import Classes
from smartwheel.api.action import Pulse


class WheelAction(BaseWheelAction):
    type = "wheel"

    def run(self, action: str, pulse: Pulse):
        wheel = Classes.WheelUi()
        if action == "wheelUp" or action == "wheelDown":
            wheel.processKey(pulse)
        elif action == "wheelSelect":
            wheel.selectModule()
            Classes.ActionEngine().wheelStateChanged(False)
        elif action == "wheelOpen":
            wheel.openWheel()
            Classes.ActionEngine().wheelStateChanged(True)

        elif action == "wheelQuickUp":
            pulse.up = True
            if pulse.virtual:
                wheel.processKey(pulse)
                return
            pulse.click = True
            Classes.ActionEngine().angleChanged(True)
            if Classes.ActionEngine().getState() == "module":
                wheel.quickSwitch(pulse)

        elif action == "wheelQuickDown":
            pulse.up = False
            if pulse.virtual:
                wheel.processKey(pulse)
                return
            pulse.click = True
            Classes.ActionEngine().angleChanged(False)
            if Classes.ActionEngine().getState() == "module":
                wheel.quickSwitch(pulse)

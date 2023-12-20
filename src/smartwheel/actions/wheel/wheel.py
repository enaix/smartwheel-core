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
            pulse.click = True
            if Classes.ActionEngine().getState() == "module":
                wheel.quickSwitch(pulse)
                Classes.ActionEngine().angleChanged(True)
            else:
                wheel.processKey(pulse)

        elif action == "wheelQuickDown":
            pulse.click = False
            if Classes.ActionEngine().getState() == "module":
                wheel.quickSwitch(pulse)
                Classes.ActionEngine().angleChanged(False)
            else:
                wheel.processKey(pulse)

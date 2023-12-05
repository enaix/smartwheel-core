from smartwheel.actions.wheel.base import BaseWheelAction

from smartwheel.api.app import Classes
from smartwheel.api.action import Pulse


class WheelAction(BaseWheelAction):
    type = "wheel"

    def run(self, action: str, pulse: Pulse):
        wheel = Classes.RootCanvas().conf["modules"][0]["class"]
        if action == "wheelUp" or action == "wheelDown":
            wheel.processKey(pulse)
        elif action == "wheelSelect":
            wheel.selectModule()
        elif action == "wheelOpen":
            wheel.openWheel()
        elif action == "wheelQuickUp":
            pulse.click = True
            wheel.quickSwitch(pulse)
        elif action == "wheelQuickDown":
            pulse.click = False
            wheel.quickSwitch(pulse)

from smartwheel.actions.wheel.base import BaseWheelAction

from smartwheel.api.app import Classes
from smartwheel.api.action import Pulse


class WheelAction(BaseWheelAction):
    type = "wheel"

    def run(self, action: str, pulse: Pulse):
        wheel = Classes.RootCanvas().conf["modules"][0]["class"]
        if action == "wheelUp":
            wheel.processKey(True, pulse)
        elif action == "wheelDown":
            wheel.processKey(False, pulse)
        elif action == "wheelSelect":
            wheel.selectModule()
        elif action == "wheelOpen":
            wheel.openWheel()
        elif action == "wheelQuickUp":
            wheel.quickSwitch(True, pulse)
        elif action == "wheelQuickDown":
            wheel.quickSwitch(False, pulse)

from smartwheel.actions.wheel.base import BaseWheelAction


class WheelAction(BaseWheelAction):
    def __init__(self):
        self.type = "wheel"

    def run(self, action, canvas, ae):
        wheel = canvas().conf["modules"][0]["class"]
        if action == "wheelUp":
            wheel.processKey(True)
        elif action == "wheelDown":
            wheel.processKey(False)
        elif action == "wheelSelect":
            wheel.selectModule()
        elif action == "wheelOpen":
            wheel.openWheel()
        elif action == "wheelQuickUp":
            wheel.quickSwitch(True)
        elif action == "wheelQuickDown":
            wheel.quickSwitch(False)

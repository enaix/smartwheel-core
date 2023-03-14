from smartwheel.actions.wheel.base import BaseWheelAction


class WheelAction(BaseWheelAction):
    def __init__(self):
        self.type = "module"

    def run(self, action, canvas, ae):
        if action in [
            "scrollUp",
            "scrollDown",
            "keyAction1",
            "keyAction2",
            "scrollUp2",
            "scrollDown2",
        ]:
            ae().action(action)

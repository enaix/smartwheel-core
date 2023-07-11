from smartwheel.actions.wheel.base import BaseWheelAction

from smartwheel.api.app import Classes
from smartwheel.api.action import Pulse


class WheelAction(BaseWheelAction):
    type = "module"

    def run(self, action: str, pulse: Pulse):
        if action in [
            "scrollUp",
            "scrollDown",
            "keyAction1",
            "keyAction2",
            "scrollUp2",
            "scrollDown2",
        ]:
            Classes.ActionEngine().action(action, pulse)

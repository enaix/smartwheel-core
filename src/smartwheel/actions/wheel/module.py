from smartwheel.actions.wheel.base import BaseWheelAction

from smartwheel.api.app import Classes
from smartwheel.api.action import Pulse, CommandActions


class WheelAction(BaseWheelAction):
    type = "module"
    actions = {CommandActions.scroll, CommandActions.keyAction1, CommandActions.keyAction2, CommandActions.scroll2}

    def run(self, action: CommandActions, pulse: Pulse):
        if action in self.actions:
            Classes.ActionEngine().action(action, pulse)

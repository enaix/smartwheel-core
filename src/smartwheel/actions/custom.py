from smartwheel.actions.baseaction import BaseAction
from smartwheel.api.action import Pulse


class Action(BaseAction):
    def run(self, context: dict, pulse: Pulse):
        event = {
            "call": context["call"],
        }
        context["module"]().processKey(event, pulse)

from smartwheel.actions.baseaction import BaseAction


class Action(BaseAction):
    def __init__(self):
        pass

    def run(self, context):
        event = {
            "canvas": context["canvas"],
            "wheel": context["wheel"],
            "call": context["call"],
        }
        context["module"]().processKey(event)

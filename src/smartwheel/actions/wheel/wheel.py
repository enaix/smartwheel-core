from smartwheel.actions.wheel.base import BaseWheelAction

from smartwheel.api.app import Classes
from smartwheel.api.action import AppState, Pulse, CommandActions


class WheelAction(BaseWheelAction):
    type = "wheel"

    def run(self, action: CommandActions, pulse: Pulse):
        wheel = Classes.WheelUi()
        if action == CommandActions.wheel:
            wheel.processKey(pulse)
        elif action == CommandActions.wheelSelect:
            wheel.selectModule()
            Classes.ActionEngine().wheelStateChanged(False)
        elif action == CommandActions.wheelOpen:
            wheel.openWheel()
            Classes.ActionEngine().wheelStateChanged(True)
        elif action == CommandActions.wheelQuick:
            if pulse.virtual:
                wheel.processKey(pulse)
                return
            pulse.click = True
            Classes.ActionEngine().angleChanged(pulse.up)
            if Classes.ActionEngine().getState() == AppState.MODULE:
                wheel.quickSwitch(pulse)


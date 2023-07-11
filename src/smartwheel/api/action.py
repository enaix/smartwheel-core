from PyQt6.QtCore import QObject
from enum import Enum


class PulseTypes(Enum):
    BUTTON = 0
    ENCODER = 1


class DevicePulse(QObject):
    """
    Pulse that is processed by action engine (must be used in serial modules)
    """

    def __init__(self, bind=None, command=None, pulse_type=None):
        super(DevicePulse, self).__init__()
        self.bind = bind
        self.command = command
        self.type = pulse_type

    bind: str = None
    """
    String that contains action bind/device name (in actionengine config)
    """

    command: str = None
    """
    String that contains device command
    """

    type: PulseTypes = None
    """
    Pulse type, can either be a button or an encoder. Buttons pulses do not have any properties
    """


class Pulse(QObject):
    """
    Pulse that is sent by actionengine, is used by modules
    """

    def __init__(self, pulse_type=None, click=True, step=None, target=None, velocity=None):
        super(Pulse, self).__init__()
        self.type = pulse_type
        self.click = click
        self.step = step
        self.target = target
        self.velocity = velocity

    type: PulseTypes = None
    """
    Pulse type, can either be a button or an encoder. Buttons pulses do not have any properties
    """

    click: bool = True
    """
    Indicates if the encoder or button has changed its position. Module should not produce any action if it is false
    """

    step: float = None
    """
    Accumulated encoder steps (from 0.0 to 1.0)
    """

    target: float = None
    """
    Encoder target position (either 0.0 or 1.0)
    """

    velocity: float = None
    """
    Current encoder velocity
    """
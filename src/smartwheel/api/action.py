from enum import Enum


class PulseTypes(Enum):
    BUTTON = 0
    ENCODER = 1


class DevicePulse:
    """
    Pulse that is processed by action engine (must be used in serial modules)
    Note that they are stored and compared by the bind property, not by the object itself.
    """

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

    up: bool = None
    """
    Scroll direction (only for the encoder)
    """

    _virtual: bool = False
    """
    (Internal) True if executed by action engine cycle
    """

    _click: bool = False
    """
    (Internal) True if virtual pulse produces a click
    """

    def __init__(self, bind=None, command=None, pulse_type=None, up=None):
        self.bind = bind
        self.command = command
        self.type = pulse_type
        self.up = up

    def copy(self):
        """
        Copy constructor of DevicePusle
        Note that it doesn't copy _virtual and _click properties
        """
        return DevicePulse(bind=self.bind, command=self.command, pulse_type=self.type, up=self.up)

    def __str__(self):
        return self.bind

    def __hash__(self):
        return hash(self.bind)

    def __eq__(self, rhs):
        if type(rhs) is DevicePulse:
            return self.bind == rhs.bind
        elif type(rhs) is str:
            return self.bind == str(rhs)
        return self.bind == rhs


class Pulse:
    """
    Pulse that is sent by actionengine, is used by modules
    """

    type: PulseTypes = None
    """
    Pulse type, can either be a button or an encoder. Buttons pulses do not have any properties
    """

    up: bool = None
    """
    True if the encoder has rotated up (clockwise). Only present if the pulse is not virtual or has changed its position (click=True)
    """

    click: bool = True
    """
    Indicates if the encoder or button has changed its position. Module should not produce any action if it is false
    """

    step: float = None
    """
    Accumulated encoder steps (from 0.0 to 360.0)
    """

    target: float = None
    """
    Encoder target position (one of the fixed angles in 0-360 range)
    """

    velocity: float = None
    """
    Current encoder velocity
    """

    virtual: bool = None
    """
    False if this pulse is created by the hardware and not by action engine cycle
    """

    def __init__(self, pulse_type=None, click=True, step=None, target=None, velocity=None, up=None):
        self.type = pulse_type
        self.click = click
        self.step = step
        self.target = target
        self.velocity = velocity
        self.up = up
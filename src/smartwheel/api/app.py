import weakref

from PyQt6.QtCore import QObject


class _Classes(QObject):
    """
    Access common application classes. Each class is referenced with weakref (you need to call it to get the object)
    Not guaranteed that some classes will be present during init
    """
    MainWindow: weakref.ref = None
    """
    MainWindow instance. Contains launch config and initializes main classes
    """

    RootCanvas: weakref.ref = None
    """
    The main class that initializes all modules, handles the wheel drawing and contains core configs
    """

    Settings: weakref.ref = None
    """
    Settings object that initializes the settings window, parses the registry, loads and executes handlers and much more
    """

    ActionEngine: weakref.ref = None
    """
    Object that processes pulses from the hardware, runs the haptics engine and calls modules
    """

    WheelUi: weakref.ref = None
    """
    Main UI element that renders the wheel, initializes sections and displays modules
    """

    # TODO add warning about import styles

    def __init__(self):
        super(_Classes, self).__init__()

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(_Classes, cls).__new__(cls)
        return cls.instance


class _Common(QObject):
    """
    Common application variables. For common module see smartwheel.common
    """

    Basedir: str = None
    """
    Base directory of the application
    """

    DebugMode: bool = None
    """
    Is debug mode enabled in the app
    This parameter enables accurate watchdogs logging
    """

    def __init__(self):
        super(_Common, self).__init__()

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(_Common, cls).__new__(cls)
        return cls.instance


Classes = _Classes()
Common = _Common()

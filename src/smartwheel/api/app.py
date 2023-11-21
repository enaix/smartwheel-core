import weakref

from PyQt6.QtCore import QObject


class _Classes(QObject):
    """
    Access common application classes. Each class is referenced with weakref
    Not guaranteed that some classes will be present during init
    """
    MainWindow: weakref.ref = None
    RootCanvas: weakref.ref = None
    Settings: weakref.ref = None
    ActionEngine: weakref.ref = None

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

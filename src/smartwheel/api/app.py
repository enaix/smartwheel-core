import weakref

from PyQt6.QtCore import QObject


class Classes(QObject):
    """
    Access common application classes. Each class is referenced with weakref
    Not guaranteed that some classes will be present during init
    """
    MainWindow: weakref.ref = None
    RootCanvas: weakref.ref = None
    Settings: weakref.ref = None

    # TODO add more classes and rewrite everything with this api
    # TODO add warning about import styles

    def __init__(self):
        super(Classes, self).__init__()

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(Classes, cls).__new__(cls)
        return cls.instance


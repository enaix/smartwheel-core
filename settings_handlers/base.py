from PyQt5.QtCore import QObject, pyqtSlot

class BaseHandler(QObject):
    """
    Base settings handler class
    """

    def __init__(self, value_getter, value_setter, parent_obj=None):
        """
        Initialize the handler

        Parameters
        ==========
        value_getter
            Property getter function (settings.SettingsWindow.getValue)
        value_setter
            Property setter function (settings.SettingsWindow.setValue)
        parent_object
            Weakref to the parent object
        """
        super(BaseHandler, self).__init__()
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.parent_obj = parent_obj

    def initElem(self, elem):
        """
        Initialize elem with specified type, must return QWidget

        Parameters
        ==========
        elem
            Element dictionary (loaded from the settings registry)
        """
        pass

    @pyqtSlot()
    def setter(self):
        """
        Setter slot, needs to be manually connected to the related widget
        """
        pass


handlers = {}

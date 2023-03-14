from PyQt6.QtCore import QObject, pyqtSlot


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

    def fetchValue(self, wid):
        """
        (Presets) Get value of the widget, must return the value or None if not supported

        Parameters
        ==========
        wid
            Widget to fetch
        """
        return None

    def updateValue(self, wid, value):
        """
        (Presets) Set the value of the widget, must return True if ok, False if not supported

        Parameters
        ==========
        wid
            Widget to update
        value
            Value to set
        """
        return False

    def linkElem(self, elem, registriesName):
        """
        (External settings registries) Link element to settings group "registriesName"

        Widget signal must be linked to settings.showLinkedWidgets(str), where str is the selected element name

        Function must return True if supported

        Parameters
        ==========
        elem
            Widget to link
        registriesName
            Widget property to set
        """
        return False


handlers = {}

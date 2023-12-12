from typing import Union, Any

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtWidgets import QWidget


class BaseHandler(QObject):
    """
    Base settings handler class
    """

    def __init__(self) -> None:
        """
        Initialize the handler
        """
        super(BaseHandler, self).__init__()

    def initElem(self, elem: dict) -> Union[QWidget, None]:
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

    def fetchValue(self, wid: QObject) -> Any:
        """
        (Presets) Get value of the widget, must return the value or None if not supported

        Parameters
        ==========
        wid
            Widget to fetch
        """
        return None

    def updateValue(self, wid: QObject, value) -> bool:
        """
        (Presets) Set the value of the widget, must return True if ok, False if not supported
        All HandlersApi.setter calls should be executed with _user=False argument
        Signals of the widget are blocked, so the setter should be called explicitly

        Parameters
        ==========
        wid
            Widget to update
        value
            Value to set
        """
        return False

    def linkElem(self, elem: QObject, registriesName: str) -> bool:
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

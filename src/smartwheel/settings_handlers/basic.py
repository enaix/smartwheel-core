import logging

from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QLabel
)
from swcolorpicker import getColor, rgb2hex, useAlpha

from smartwheel.settings_handlers.base import BaseHandler
from smartwheel.api.settings import HandlersApi


class IntHandler(BaseHandler):
    def __init__(self):
        super(IntHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QSpinBox()
        if elem.get("min") is not None:
            wid.setMinimum(elem["min"])
        if elem.get("max") is not None:
            wid.setMaximum(elem["max"])

        ok, value = HandlersApi.getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setValue(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.valueChanged.connect(self.setInt)

        return wid

    @pyqtSlot(int)
    def setInt(self, value):
        caller = self.sender()
        HandlersApi.setter(caller, value)

    def fetchValue(self, wid):
        return wid.value()

    def updateValue(self, wid, value):
        wid.setValue(value)
        HandlersApi.setter(wid, value, _user=False)
        return True


class FloatHandler(BaseHandler):
    def __init__(self):
        super(FloatHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QDoubleSpinBox()

        if elem.get("step") is not None:
            wid.setSingleStep(elem["step"])

        if elem.get("min") is not None:
            wid.setMinimum(elem["min"])
        if elem.get("max") is not None:
            wid.setMaximum(elem["max"])

        ok, value = HandlersApi.getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setValue(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.valueChanged.connect(self.setFloat)

        return wid

    @pyqtSlot(float)
    def setFloat(self, value):
        caller = self.sender()
        HandlersApi.setter(caller, value)

    def fetchValue(self, wid):
        return wid.value()

    def updateValue(self, wid, value):
        wid.setValue(value)
        HandlersApi.setter(wid, value, _user=False)
        return True


class StringHandler(BaseHandler):
    def __init__(self):
        super(StringHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QLineEdit()

        ok, value = HandlersApi.getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setText(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.textChanged.connect(self.setStr)

        return wid

    @pyqtSlot(str)
    def setStr(self, value):
        caller = self.sender()
        HandlersApi.setter(caller, value)

    def fetchValue(self, wid):
        return wid.text()

    def updateValue(self, wid, value):
        wid.setText(value)
        HandlersApi.setter(wid, value, _user=False)
        return True


class ColorHandler(BaseHandler):
    def __init__(self):
        super(ColorHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def setIcon(self, wid, color):
        pix = QPixmap(100, 100)
        pix.fill(color)
        icon = QIcon(pix)
        wid.setIcon(icon)

    def initElem(self, elem):
        wid = QPushButton()

        wid.setStyleSheet("QPushButton { text-align: left; }")

        wid.setProperty("module", elem["module"])
        wid.setProperty("prop", elem["prop"])
        wid.setProperty("index", elem.get("index"))

        ok, value = HandlersApi.getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setText(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        if value is None:
            value = "#000000"

        self.setIcon(wid, QColor(value))

        wid.clicked.connect(self.setColor)

        return wid

    @pyqtSlot()
    def setColor(self):
        caller = self.sender()
        color = QColor(caller.text()).getRgb()
        if len(color) == 4:
            useAlpha(True)

        new_color = "#" + rgb2hex(getColor(color))
        if not color == new_color:
            HandlersApi.setter(caller, new_color)
            self.setIcon(caller, QColor(new_color))
            caller.setText(new_color)

    def fetchValue(self, wid):
        return wid.text()

    def updateValue(self, wid, value):
        module = wid.property("module")
        prop = wid.property("prop")
        index = wid.property("index")

        if module is None or prop is None:
            self.logger.warning("Could not get color picker properties")
            return False

        wid.setText(value)
        self.setIcon(wid, QColor(value))
        HandlersApi.setter(value=value, module=module, prop=prop, index=index, _user=False)
        return True


class BoolHandler(BaseHandler):
    def __init__(self):
        super(BoolHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QCheckBox()

        ok, value = HandlersApi.getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setChecked(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.toggled.connect(self.setBool)

        return wid

    @pyqtSlot(bool)
    def setBool(self, value):
        caller = self.sender()
        HandlersApi.setter(caller, value)

    def fetchValue(self, wid):
        return wid.isChecked()

    def updateValue(self, wid, value):
        wid.setChecked(value)
        HandlersApi.setter(wid, value, _user=False)
        return True


class CComboBox(QComboBox):
    opened = pyqtSignal()

    def showPopup(self) -> None:
        self.opened.emit()
        super(CComboBox, self).showPopup()

class ComboHandler(BaseHandler):
    def __init__(self):
        super(ComboHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = CComboBox()

        if type(elem["options"]) == list:
            wid.insertItems(0, elem["options"])
        else:
            # Need to get options programmatically
            ok, ops = HandlersApi.getter(
                module=elem["options"]["module"],
                prop=elem["options"]["prop"],
                index=elem["options"].get("index"),
            )
            if not ok:
                self.logger.error(
                    "Could not get combo items from "
                    + elem["options"]["module"]
                    + "."
                    + elem["options"]["prop"]
                )
                return None
            wid.setProperty("options", {"module": elem["options"]["module"],
                                        "prop": elem["options"]["prop"],
                                        "index": elem["options"].get("index")})

            wid.insertItems(0, ops)
            if elem.get("dynamic", False):
                wid.opened.connect(self.getOps, Qt.ConnectionType.QueuedConnection)

        ok, value = HandlersApi.getter(elem["module"], elem["prop"])
        if ok:
            wid.setCurrentText(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.currentTextChanged.connect(self.setStr)

        return wid

    @pyqtSlot(str)
    def setStr(self, value):
        caller = self.sender()
        HandlersApi.setter(caller, value)

    @pyqtSlot()
    def getOps(self):
        caller = self.sender()
        ops = caller.property("options")
        if ops is None:
            self.logger.warning("Could not get combo options list")
            return

        ok, ops = HandlersApi.getter(module=ops["module"], prop=ops["prop"], index=ops.get("index"))
        if not ok:
            self.logger.warning("Could not update combo options list")
            return

        caller.clear()
        caller.insertItems(0, ops)

    def fetchValue(self, wid):
        return wid.currentText()

    def updateValue(self, wid, value):
        wid.setCurrentText(value)
        HandlersApi.setter(wid, value, _user=False)
        return True

    def linkElem(self, elem, registriesName):
        elem.setProperty("registriesName", registriesName)
        elem.currentTextChanged.connect(HandlersApi._showLinkedWidgets)
        return True


class Watcher(QLabel):
    def __init__(self, module: str, prop: str, index: int = None):
        super(Watcher, self).__init__()
        self.module = module
        self.prop = prop
        self.index = index

    def fetch(self):
        return HandlersApi.getter(self.module, self.prop, self.index, silent=True)

    def setVar(self, ok: bool, var):
        if not ok and self.isEnabled():
            var = "?"
            self.setDisabled(True)
        elif ok and not self.isEnabled():
            self.setDisabled(False)

        self.setText(str(var))
        return ok


class WatchHandler(BaseHandler):
    def __init__(self):
        super(WatchHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = Watcher(elem["module"], elem["prop"], elem.get("index"))

        ok, val = wid.fetch()
        wid.setVar(ok, val)

        if not ok and not elem.get("noWarn", False):
            self.logger.warning("Could not enable variable watcher for " + elem["name"])

        HandlersApi._addVariableWatch(wid, val)

        return wid

    def fetchValue(self, wid):
        return None

    def updateValue(self, wid, value):
        return False


class ExternalHandler(BaseHandler):
    def __init__(self):
        super(ExternalHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QPushButton(elem.get("text", "..."))

        registry = HandlersApi.externalRegistries.get(elem.get("registry"))
        if registry is None:
            self.logger.warning("Could not find external registry " + elem.get("registry", "None"))
            return wid
        wid.clicked.connect(registry.show)

        return wid

    def fetchValue(self, wid):
        return None

    def updateValue(self, wid, value):
        return False


class TextHandler(BaseHandler):
    def __init__(self):
        super(TextHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QLabel(elem["text"])

        wid.setDisabled(True)

        return wid

    def fetchValue(self, wid):
        return None

    def updateValue(self, wid, value):
        return False


handlers = {
    "int": IntHandler,
    "float": FloatHandler,
    "string": StringHandler,
    "color": ColorHandler,
    "bool": BoolHandler,
    "combo": ComboHandler,
    "watch": WatchHandler,
    "external": ExternalHandler,
    "text": TextHandler
}

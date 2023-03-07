import logging

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
)
from swcolorpicker import getColor, rgb2hex, useAlpha

from .base import BaseHandler


class IntHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(IntHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QSpinBox()
        if elem.get("min") is not None:
            wid.setMinimum(elem["min"])
        if elem.get("max") is not None:
            wid.setMaximum(elem["max"])

        ok, value = self.value_getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setValue(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.valueChanged.connect(self.setInt)

        return wid

    @pyqtSlot(int)
    def setInt(self, value):
        caller = self.sender()
        self.value_setter(caller, value)

    def fetchValue(self, wid):
        return wid.value()

    def updateValue(self, wid, value):
        wid.setValue(value)
        return True


class FloatHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(FloatHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QDoubleSpinBox()

        if elem.get("step") is not None:
            wid.setSingleStep(elem["step"])

        if elem.get("min") is not None:
            wid.setMinimum(elem["min"])
        if elem.get("max") is not None:
            wid.setMaximum(elem["max"])

        ok, value = self.value_getter(elem["module"], elem["prop"], elem.get("index"))
        if ok:
            wid.setValue(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.valueChanged.connect(self.setFloat)

        return wid

    @pyqtSlot(float)
    def setFloat(self, value):
        caller = self.sender()
        self.value_setter(caller, value)

    def fetchValue(self, wid):
        return wid.value()

    def updateValue(self, wid, value):
        wid.setValue(value)
        return True


class StringHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(StringHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QLineEdit()

        ok, value = self.value_getter(elem["module"], elem["prop"])
        if ok:
            wid.setText(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.textChanged.connect(self.setStr)

        return wid

    @pyqtSlot(str)
    def setStr(self, value):
        caller = self.sender()
        self.value_setter(caller, value)

    def fetchValue(self, wid):
        return wid.text()

    def updateValue(self, wid, value):
        wid.setText(value)
        return True


class ColorHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ColorHandler, self).__init__(value_getter, value_setter, parent_obj)
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

        ok, value = self.value_getter(elem["module"], elem["prop"])
        if ok:
            wid.setText(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

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
            self.value_setter(caller, new_color)
            self.setIcon(caller, QColor(new_color))
            caller.setText(new_color)

    def fetchValue(self, wid):
        return wid.text()

    def updateValue(self, wid, value):
        module = wid.property("module")
        prop = wid.property("prop")

        if module is None or prop is None:
            self.logger.warning("Could not get color picker properties")
            return False

        wid.setText(value)
        self.setIcon(wid, QColor(value))
        self.value_setter(value=value, module=module, prop=prop)
        return True


class BoolHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(BoolHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QCheckBox()

        ok, value = self.value_getter(elem["module"], elem["prop"])
        if ok:
            wid.setChecked(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.clicked.connect(self.setBool)

        return wid

    @pyqtSlot(bool)
    def setBool(self, value):
        caller = self.sender()
        self.value_setter(caller, value)

    def fetchValue(self, wid):
        return wid.isChecked()

    def updateValue(self, wid, value):
        wid.setChecked(value)
        return True


class ComboHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ComboHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QComboBox()

        wid.insertItems(0, elem["options"])

        ok, value = self.value_getter(elem["module"], elem["prop"])
        if ok:
            wid.setCurrentText(value)
        else:
            self.logger.warning("Could not get value for " + elem["name"])

        wid.currentTextChanged.connect(self.setStr)

        return wid

    @pyqtSlot(str)
    def setStr(self, value):
        caller = self.sender()
        self.value_setter(caller, value)

    def fetchValue(self, wid):
        return wid.currentText()

    def updateValue(self, wid, value):
        wid.setCurrentText(value)
        return True


handlers = {
    "int": IntHandler,
    "float": FloatHandler,
    "string": StringHandler,
    "color": ColorHandler,
    "bool": BoolHandler,
    "combo": ComboHandler,
}

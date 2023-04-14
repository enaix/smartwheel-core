import logging
import math

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QComboBox, QGridLayout, QSizePolicy, QVBoxLayout, QWidget

from smartwheel.settings_handlers.base import BaseHandler


class UIModulesLoader(BaseHandler):
    """
    UI modules loader
    """

    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(UIModulesLoader, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        """
        Load ui modules picker

        Parameters
        ==========
        elem
            Element from config
        """
        ok, modules = self.value_getter("canvas", "modules")
        if not ok:
            self.logger.error("Could not get ui modules")
            return None

        ok, modulesLoad = self.value_getter("canvas", "modulesLoad")
        if not ok:
            self.logger.error("Could not get loaded ui modules")
            return None

        elem["modules"] = modules
        elem["modulesLoad"] = modulesLoad
        elem["disabled"] = [0]

        picker = self.parent_obj().handlers["modules"].initElem(elem)
        if picker is None:
            self.logger.error("Could not initialize modules picker")
            return None

        layout = picker.findChild(QVBoxLayout).findChild(QGridLayout)

        for i in range(1, layout.rowCount()):
            if layout.itemAtPosition(i, 0) is None:
                break

            checked = layout.itemAtPosition(i, 0).widget()
            checked.clicked.connect(self.setEnabled)

        return picker

    @pyqtSlot(bool)
    def setEnabled(self, enabled):
        caller = self.sender()

        name = caller.property("name")

        ok, modules = self.value_getter("canvas", "modules")
        if not ok:
            self.logger.error("Could not get ui modules")
            return

        ok, modulesLoad = self.value_getter("canvas", "modulesLoad")
        if not ok:
            self.logger.error("Could not get loaded ui modules")
            return

        index = None
        for i in range(len(modules)):
            if modules[i]["name"] == name:
                index = i
                break

        if index is None:
            self.logger.error("Could not get module by name")
            return

        if enabled:
            m_set = set(modulesLoad)
            m_set.add(index)
            modulesLoad = list(m_set)
        else:
            modulesLoad.remove(index)

        self.value_setter(module="canvas", prop="modulesLoad", value=modulesLoad)


class SelectorWheel(QWidget):
    def __init__(self, n_sections):
        super(SelectorWheel, self).__init__()
        self.combos = []

        for a in range(0, 360, 360 // n_sections):
            combo = QComboBox(parent=self)
            # combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            # combo.setFixedSize(10, 10)
            combo.move(
                self.x() + int(100 + 100 * math.cos(math.radians(a))),
                self.y() + int(100 + 100 * math.sin(math.radians(a))),
            )
            self.combos.append(combo)


class WheelPicker(BaseHandler):
    """
    Wheel sections picker
    """

    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(WheelPicker, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        """
        Initialize picker

        Parameters
        ==========
        elem
            Wheel elem config
        """
        ok, num_sections = self.value_getter("common", "selectionWheelEntries")
        if not ok:
            self.logger.warning("Could not get selection wheel entries number")
            return

        wrapper = SelectorWheel(num_sections)

        return wrapper


handlers = {"uimodules": UIModulesLoader, "sections": WheelPicker}

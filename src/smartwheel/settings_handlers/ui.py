from smartwheel.settings_handlers.base import BaseHandler

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QVBoxLayout, QGridLayout

import logging

class UIModulesLoader(BaseHandler):
    """
    UI modules picker
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


handlers = {"uimodules": UIModulesLoader}

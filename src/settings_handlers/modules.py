from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .base import BaseHandler
import logging

class ModulesLoader(BaseHandler):
    """
    Common modules picker
    """
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ModulesLoader, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        """
        Initialize modules picker, should not be called directly from settings.py

        Parameters
        ==========
        elem
            Dict containing modules {"modules": [{"name": "internalName", "title": ..., "description": ...,}, ...], "modulesLoad": [0, 1, ...]}
        """
        layout = QGridLayout()

        font = QFont()
        font.setBold(True)
        
        labels = [QLabel(x) for x in ["Enabled", "Title", "Description", "Options"]]
        
        for i in range(len(labels)):
            labels[i].setFont(font)
            layout.addWidget(labels[i], 0, i, Qt.AlignLeft)

        for i, mod in enumerate(elem["modules"]):
            check = QCheckBox()
            options = QPushButton("...")

            for j, s in enumerate(["title", "description"]):
                label = QLabel(mod[s])

                layout.addWidget(label, i+1, j+1, Qt.AlignLeft)

            layout.addWidget(check, i+1, 0, Qt.AlignLeft)
            layout.addWidget(options, i+1, 3, Qt.AlignLeft)

            for j in range(1, 4):
                if layout.itemAtPosition(i+1, j) is not None:
                    check.clicked.connect(layout.itemAtPosition(i+1, j).widget().setEnabled)
                    if not check.isChecked():
                        layout.itemAtPosition(i+1, j).widget().setDisabled(True)

        wrapper = QWidget()
        wrapper.setLayout(layout)

        return wrapper


class SerialLoader(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(SerialLoader, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        ok, modules = self.value_getter("canvas", "serialModules")
        if not ok:
            self.logger.error("Could not get serial modules")
            return None

        ok, modulesLoad = self.value_getter("canvas", "serialModulesLoad")
        if not ok:
            self.logger.error("Could not get loaded serial modules")
            return None
        
        elem["modules"] = modules
        elem["modulesLoad"] = modulesLoad

        picker = self.parent_obj().handlers["modules"].initElem(elem)
        if picker is None:
            self.logger.error("Could not initialize modules picker")
            return None
        
        return picker


handlers = {"modules": ModulesLoader, "serial": SerialLoader}

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QSpinBox, QComboBox, QPushButton
from .base import BaseHandler
import logging
import os


class PresetHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(PresetHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        wid = QComboBox()

        preset_files = [x for x in os.listdir(os.path.join("presets", elem["folder"])) if x.endswith(".json")]

        presets = []
        preset_names = []

        for p in preset_files:
            with open(os.path.join("presets", elem["folder"], p), 'r') as f:
                presets.append(json.load(f))
        for p in presets:
            preset_names.append(p["title"])

        preset_names.append("Custom")

        self.value_setter(module="settings", prop="presets." + str(elem["tab_index"]))

        wid.insertItems(len(preset_names) - 1, preset_names)
        wid.setProperty("tab_index", elem["tab_index"])

        wid.currentIndexChanged.connect(self.setPreset)

        return wid

    @pyqtSlot(int)
    def setPreset(self, value):
        caller = self.sender()
        ind = caller.property("tab_index")
        if ind is None:
            self.logger.warning("Could not get tab index from the preset picker")

        preset = caller.currentText()

        self.parent_obj.loadPreset(ind, preset)


handlers = {"preset": PresetHandler}

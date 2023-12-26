import json
import logging
import os
import weakref

from PyQt6.QtCore import pyqtSlot, QSize
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QPushButton,
    QWidget, QSizePolicy,
)

from smartwheel.settings_handlers.base import BaseHandler
from smartwheel.api.settings import HandlersApi


class PresetHandler(BaseHandler):
    def __init__(self):
        super(PresetHandler, self).__init__()
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        layout = QHBoxLayout()
        wid = QComboBox()
        ok, self.basedir = HandlersApi.getter(module="canvas", prop="basedir")

        wid.setProperty("presets_folder", elem["folder"])

        p_path = os.path.join(self.basedir, "presets", elem["folder"])

        if not os.path.exists(p_path):
            os.makedirs(p_path, exist_ok=True)

        preset_files = [x for x in os.listdir(p_path) if x.endswith(".json")]

        presets = {}
        preset_names = []

        for p in preset_files:
            with open(
                os.path.join(self.basedir, "presets", elem["folder"], p), "r"
            ) as f:
                pr = json.load(f)
                presets[pr["name"]] = pr

        for _, p in presets.items():
            preset_names.append(p["title"])

        preset_names.append("Custom")

        HandlersApi.setter(
            value=presets, module="settings", prop="presets." + str(elem["tab_index"]), _user=False
        )

        wid.insertItems(len(preset_names) - 1, preset_names)
        wid.setProperty("tab_index", elem["tab_index"])
        wid.setProperty("module", elem["module"])
        wid.setProperty("prop", elem["prop"])

        wid.currentIndexChanged.connect(self.setPreset)

        ok, value = HandlersApi.getter(elem["module"], elem["prop"])
        if not ok:
            value = "Custom"

        wid.blockSignals(True)
        wid.setCurrentText(value)
        wid.blockSignals(False)
        wid.currentIndexChanged.emit(wid.currentIndex())

        save = QPushButton()
        save.setIcon(HandlersApi.icons["save-outline"])
        save.setIconSize(QSize(20, 20))
        save.setProperty("combo", weakref.ref(wid))
        save.clicked.connect(self.savePreset)

        layout.addWidget(wid)
        layout.addWidget(save)

        wrapper = QWidget()
        wrapper.setLayout(layout)
        return wrapper

    def parsePresetName(self, title):
        """
        Convert preset title to the internal preset name ("Arctic Flat" -> "arctic_flat")

        Parameters
        ==========
        title
            Title to convert
        """
        return "".join(
            [
                x if x.isalnum or x == "_" else ""
                for x in title.lower().replace(" ", "_")
            ]
        )

    @pyqtSlot()
    def savePreset(self):
        """
        Save current preset, must be called by the Save button
        """
        caller = self.sender().property("combo")
        if caller is None:
            self.logger.warning("Could not get linked combo box")
            return

        ind = caller().property("tab_index")
        folder = caller().property("presets_folder")
        module = caller().property("module")
        prop = caller().property("prop")

        if ind is None:
            self.logger.warning("Could not get tab index from the preset picker")
            return
        if folder is None:
            self.logger.warning(
                "Could not get presets folder name from the preset picker"
            )
            return
        if module is None or prop is None:
            self.logger.warning("Could not get presets picker properties")
            return

        preset = caller().currentText()

        if preset == "Custom":
            title, ok = QInputDialog().getText(
                self.sender(),
                "New preset",
                "Preset name:",
                QLineEdit.EchoMode.Normal,
                "Preset" + str(caller().currentIndex() + 1),
            )

            if not ok or not title:
                self.logger.info("Input dialog closed")
                return

            if caller().findText(title) == -1:
                new_ind = caller().count() - 1
                caller().insertItem(new_ind, title)
                caller().blockSignals(True)
                caller().setCurrentIndex(new_ind)
                caller().blockSignals(False)
                HandlersApi.setter(value=title, module=module, prop=prop)
        else:
            title = preset

        name = self.parsePresetName(title)

        HandlersApi._savePreset(
            ind,
            name,
            title,
            os.path.join(self.basedir, "presets", folder, name + ".json"),
        )

    @pyqtSlot(int)
    def setPreset(self, value):
        """
        Load the preset from the combo

        Parameters
        ==========
        value
            Combo index
        """
        caller = self.sender()
        ind = caller.property("tab_index")
        module = caller.property("module")
        prop = caller.property("prop")

        if ind is None:
            self.logger.warning("Could not get tab index from the preset picker")
        if module is None or prop is None:
            self.logger.warning("Could not get presets picker properties")
            return

        preset = caller.currentText()

        HandlersApi.setter(value=preset, module=module, prop=prop)

        if preset == "Custom":
            return

        HandlersApi._loadPreset(ind, self.parsePresetName(preset))


handlers = {"preset": PresetHandler}

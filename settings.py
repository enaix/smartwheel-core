from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QSpacerItem, \
    QSizePolicy, QGroupBox, QSpinBox, QLabel, QFormLayout, QScrollArea
import json
import logging
import os


class SettingsWindow(QWidget):
    def __init__(self, config_file, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.conf = None
        self.logger = logging.getLogger(__name__)
        self.loadConfig(config_file)

        self.initLayout()

    def loadConfig(self, config_file):
        with open(config_file, "r") as f:
            self.conf = json.load(f)

        if self.conf.get("tabs") is not None:
            for i in range(len(self.conf["tabs"])):
                with open(os.path.join("settings_registry", self.conf["tabs"][i]["config"]), "r") as f:
                    self.conf["tabs"][i]["conf"] = json.load(f)

    def initTab(self, index):
        tab = self.conf["tabs"][index]
        scroll = QScrollArea()
        layout = QVBoxLayout()

        for elem_group in tab["conf"]["items"]:
            form = QFormLayout()
            group = QGroupBox(elem_group["name"])
            for elem in elem_group["options"]:
                label = QLabel(elem["name"])
                wid = None
                if elem["type"] == "int":
                    wid = QSpinBox()
                    if elem.get("min") is not None:
                        wid.setMinimum(elem["min"])
                    if elem.get("max") is not None:
                        wid.setMaximum(elem["max"])

                if wid is not None:
                    form.addRow(label, wid)

            group.setLayout(form)
            layout.addWidget(group)

        scroll.setLayout(layout)

        return scroll

    def initLayout(self):
        baseLayout = QVBoxLayout(self)

        tabWidget = QTabWidget()
        for i in range(len(self.conf["tabs"])):
            scroll = self.initTab(i)
            tabWidget.addTab(scroll, self.conf["tabs"][i]["name"])

        baseLayout.addWidget(tabWidget)

        bottomPanel = QHBoxLayout()
        okButton = QPushButton("OK")
        applyButton = QPushButton("Apply")
        cancelButton = QPushButton("Cancel")
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        bottomPanel.addSpacerItem(spacer)
        bottomPanel.addWidget(cancelButton)
        bottomPanel.addWidget(applyButton)
        bottomPanel.addWidget(okButton)

        baseLayout.addLayout(bottomPanel)

        self.setLayout(baseLayout)

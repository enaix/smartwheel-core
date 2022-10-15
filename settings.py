from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QSpacerItem, QSizePolicy
import json
import logging


class SettingsWindow(QWidget):
    def __init__(self, config_file, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.loadConfig(config_file)

        self.initLayout()

    def loadConfig(self, config_file):
        with open("config.json", "r") as f:
            self.conf = json.load(f)

    def initLayout(self):
        baseLayout = QVBoxLayout(self)

        tabWidget = QTabWidget()
        #tabWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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

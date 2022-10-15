# from PyQt5.QtGui import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QSpacerItem, \
    QSizePolicy, QGroupBox, QSpinBox, QLabel, QFormLayout, QScrollArea, QLineEdit, QComboBox, QCheckBox, QDoubleSpinBox
import json
import logging
import os


class SettingsWindow(QWidget):
    def __init__(self, config_file, main_class, conf_class, parent=None):
        """
        Init SettingsWindow
        
        Parameters
        ==========
        config_file
            Path to settings registry
        main_class
            Weakref to RootWindow object
        conf_class
            Weakref to WConfig object
        """
        super(SettingsWindow, self).__init__(parent)
        self.hook = None
        self.conf = None
        self.settings = {}
        self.logger = logging.getLogger(__name__)
        self.loadConfig(config_file)
        self.setConfigHook(main_class, conf_class)

        self.initLayout()

    def loadConfig(self, config_file):
        """
        Import settings registry

        Parameters
        ==========
        config_file
            Settings registry config.json file
        """
        with open(config_file, "r") as f:
            self.conf = json.load(f)

        if self.conf.get("tabs") is not None:
            for i in range(len(self.conf["tabs"])):
                with open(os.path.join("settings_registry", self.conf["tabs"][i]["config"]), "r") as f:
                    self.conf["tabs"][i]["conf"] = json.load(f)

    def setConfigHook(self, main_class, conf):
        """
        Set hooks for the settings class in order to load/save global settings

        Parameters
        ==========
        main_class
            Weakref to RootWindow object
        conf
            Weakref to WConfig object
        """
        self.settings["main"] = conf().c
        self.settings["canvas"] = main_class().rc.conf
        self.settings["common"] = main_class().rc.common_config
        self.settings["settings"] = self.conf

        # Parsing serial modules
        self.settings["serial"] = {}
        serial = main_class().serialModules

        for name in main_class().serialModulesNames:
            if hasattr(serial[name], "conf"):
                self.settings["serial"][name] = serial[name].conf
            else:
                self.logger.error("serialpipe." + name + " has no conf attribute")

        # Parsing canvas section modules
        self.settings["modules"] = {}
        modules = main_class().rc.conf["modules"]

        for mod in modules:
            if mod.get("class") is not None:
                if hasattr(mod["class"], "conf"):
                    self.settings[mod["name"]] = mod["class"].conf
                else:
                    self.logger.error(mod["name"] + " has no conf attribute")

    def getValue(self, module, prop, index=None):
        """
        Get property from the application
        
        Parameters
        ==========
        module
            Module name (in self.settings)
        prop
            Property keys, separated by `.`
        index
            If not None, the index in the property array. If an array, then it's duplicated at specified indices
        """
        if self.settings.get(module) is None:
            self.logger.error("Could not get value: no module " + module)
            return False, None

        props = prop.split('.')
        cur_prop = self.settings[module]
        for p in props:
            if cur_prop.get(p) is None:
                self.logger.error("Could not get value: no property " + module + "." + prop)
                return False, None
            else:
                cur_prop = cur_prop[p]

        if index is None:
            return True, cur_prop
        elif type(index) == list:
            return True, cur_prop[index[0]]
        else:
            return True, cur_prop[index]

    def initTab(self, index):
        """
        Parse registry and generate elements

        Parameters
        ==========
        index
            Tab index
        """
        tab = self.conf["tabs"][index]
        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout()
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

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

                    ok, value = self.getValue(elem["module"], elem["prop"], elem.get("index"))
                    if ok:
                        wid.setValue(value)
                    else:
                        self.logger.warning("Could not get value for " + elem["name"])

                elif elem["type"] == "float":
                    wid = QDoubleSpinBox()

                    if elem.get("step") is not None:
                        wid.setSingleStep(elem["step"])

                    if elem.get("min") is not None:
                        wid.setMinimum(elem["min"])
                    if elem.get("max") is not None:
                        wid.setMaximum(elem["max"])

                    ok, value = self.getValue(elem["module"], elem["prop"], elem.get("index"))
                    if ok:
                        wid.setValue(value)
                    else:
                        self.logger.warning("Could not get value for " + elem["name"])

                elif elem["type"] == "string":
                    wid = QLineEdit()
                    ok, value = self.getValue(elem["module"], elem["prop"])
                    if ok:
                        wid.setText(value)
                    else:
                        self.logger.warning("Could not get value for " + elem["name"])

                elif elem["type"] == "combo":
                    wid = QComboBox()
                    wid.insertItems(0, elem["options"])
                    ok, value = self.getValue(elem["module"], elem["prop"])
                    if ok:
                        wid.setCurrentText(value)
                    else:
                        self.logger.warning("Could not get value for " + elem["name"])

                elif elem["type"] == "bool":
                    wid = QCheckBox()
                    ok, value = self.getValue(elem["module"], elem["prop"])
                    if ok:
                        wid.setChecked(value)
                    else:
                        self.logger.warning("Could not get value for " + elem["name"])

                if wid is not None:
                    wid.setMinimumWidth(self.conf["fieldWidth"])
                    wid.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
                    widWrapper = QHBoxLayout()
                    spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
                    widWrapper.addSpacerItem(spacer)
                    widWrapper.addWidget(wid)
                    form.addRow(label, widWrapper)

            group.setLayout(form)
            layout.addWidget(group)

        wrapper.setLayout(layout)
        scroll.setWidget(wrapper)

        return scroll

    def initLayout(self):
        """
        Generate layout
        """
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

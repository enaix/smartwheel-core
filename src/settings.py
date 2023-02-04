# from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QSpacerItem, \
    QSizePolicy, QGroupBox, QFormLayout, QScrollArea, QLabel
import json
import logging
import os
import weakref
import importlib
import common


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
        self.setWindowTitle("Settings")
        self.hook = None
        self.conf = None
        self.handlers_conf = None
        self.handlers = None
        self.settings = {}
        self.logger = logging.getLogger(__name__)
        self.loadConfig(config_file)
        self.setConfigHook(main_class, conf_class)
        self.loadSettingsHandlers(self.conf["settings_handlers_dir"])

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
        self.main_class = main_class  # weakref to the main class
        self.confClass = conf  # weakref to wconfig
        self.settings["main"] = conf().c
        self.settings["canvas"] = main_class().rc.conf
        self.settings["common"] = main_class().rc.common_config
        self.settings["settings"] = self.conf
        self.settings["actionengine"] = main_class().rc.ae.conf

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
        main_modules = main_class().rc.conf["modules"]
        wheel_modules = main_class().rc.wheel_modules

        for i, modules in enumerate([main_modules, wheel_modules]):
            for mod in modules:
                if mod.get("class") is not None:
                    if hasattr(mod["class"], "conf"):
                        self.settings[mod["name"]] = mod["class"].conf
                    else:
                        self.logger.error(mod["name"] + " has no conf attribute")
                else:
                    if i == 1:
                        self.logger.error(mod["name"] + " has no class attribute")

    def loadSettingsHandlers(self, handlers_dir):
        """
        Init settings handlers from the directory
        
        Parameters
        ==========
        handlers_dir
            Directory containing settings handlers, must contain config.json file
        """
        s_config = os.path.join(handlers_dir, "config.json")
        if not os.path.exists(s_config):
            self.logger.error("Missing " + s_config + " file")
            os.exit(1)

        with open(s_config, 'r') as f:
            self.handlers_conf = json.load(f)

        self.handlers = {}
        for mod_name in self.handlers_conf["handlers_modules"]:
            handler = importlib.import_module(self.conf["settings_handlers_dir"] + "." + mod_name)
            h_dict = handler.handlers
            for k in h_dict:
                if self.handlers.get(k) is not None:
                    self.logger.warning("Setting handler " + k + " is defined twice. Overriding")
                self.handlers[k] = h_dict[k](self.getValue, self.setValue, weakref.ref(self))

    def getValue(self, module, prop, index=None):
        """
        Get property from the application
        Returns (True, value) if found, (False, None) otherwise

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

    def dictWalk(self, d, props, value, index=None, _i=0):
        """
        Recursively walk in nested dicts and apply value

        Parameters
        ==========
        d
            Target dict
        props
            List of keys
        value
            Value to apply
        index
            If not None, the index in the property array. If an array, then it's duplicated at specified indices
        _i
            (Private) Recursion depth
        """

        key = "_" + str(_i)

        if _i != 0:
            key = "_" + str(_i-1)
        
        # We create the wrapper if needed
        if d.get(key) is None:
            w = {key: d}
        else:
            w = d

        if len(props) == 1:
            if index is None:
                w[key][props[0]] = value
            elif type(index) == list:
                for i in index:
                    w[key][props[0]][i] = value
            else:
                w[key][props[0]][index] = value
            return

        # Python reference hack, we use a mutable type as a wrapper
        wrapper = {"_"+str(_i): w[key][props[0]]}

        self.dictWalk(wrapper, props[1:], value, index, _i+1)

    def setValue(self, obj=None, value=None, module=None, prop=None, index=None):
        """
        Set property from the application.
        Module, prop and index arguments may be fetched from the object properties (passing only obj and value) or passed directly (module, prop, index (optional) and value)
        
        Parameters
        ==========
        obj
            (Optional) QObject (widget) with `module`, `prop` (and `index`) properties
        value
            (Optional) Value to set
        module
            (Optional) Module name (in self.settings)
        prop
            (Optional) Property keys, separated by `.`
        index
            (Optional) If not None, the index in the property array. If an array, then it's duplicated at specified indices
        """

        if obj is not None:
            module = obj.property("widmodule")
            prop = obj.property("prop")
            index = obj.property("index")

        if module is None:
            self.logger.error("Could not obtain module value")

        if self.settings.get(module) is None:
            self.logger.error("Could not get value: no module " + str(module))
            return

        props = prop.split('.')

        self.dictWalk(self.settings[module], props, value, index)

        self.main_class().update()

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
                if elem.get("name") is not None:
                    label = QLabel(elem["name"])
                else:
                    label = None

                wid = None

                if self.handlers.get(elem["type"]) is None:
                    self.logger.error("Could not find the handler for type " + elem["type"])
                else:
                    wid = self.handlers[elem["type"]].initElem(elem)

                if wid is not None:
                    if elem.get("module") is not None:
                        wid.setProperty("widmodule", elem["module"])
                    if elem.get("prop") is not None:
                        wid.setProperty("prop", elem["prop"])
                    if elem.get("index") is not None:
                        wid.setProperty("index", elem["index"])

                    wid.setMinimumWidth(self.conf["fieldWidth"])
                    wid.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
                    widWrapper = QHBoxLayout()
                    spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
                    widWrapper.addSpacerItem(spacer)
                    widWrapper.addWidget(wid)
                    
                    if label is not None:
                        form.addRow(label, widWrapper)
                    else:
                        form.addRow(widWrapper)

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
        okButton.clicked.connect(common.config_manager.saveConfig)
        okButton.clicked.connect(self.close)

        applyButton = QPushButton("Apply")
        applyButton.clicked.connect(common.config_manager.saveConfig)

        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        bottomPanel.addSpacerItem(spacer)
        bottomPanel.addWidget(cancelButton)
        bottomPanel.addWidget(applyButton)
        bottomPanel.addWidget(okButton)

        baseLayout.addLayout(bottomPanel)

        self.setLayout(baseLayout)

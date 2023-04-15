# from PyQt6.QtGui import *
import importlib
import json
import logging
import os
import weakref
from queue import LifoQueue

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from smartwheel import common, config


class SettingsWindow(QWidget):
    def __init__(
        self, config_file, defaults_file, main_class, conf_class, basedir, parent=None
    ):
        """
        Init SettingsWindow

        Parameters
        ==========
        config_file
            Path to settings registry config
        defaults_file
            Path to settings registry default config
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
        self.basedir = basedir
        self.settings = {}
        self.external_reg = {}
        self.logger = logging.getLogger(__name__)
        self.loadConfig(config_file, defaults_file)
        self.setConfigHook(main_class, conf_class)
        self.loadSettingsHandlers(
            os.path.join(self.basedir, self.conf["settings_handlers_dir"])
        )
        self.preset_tabs = {}
        self.preset_controllers = {}
        self.presets_index_mapping = {}
        self.conf["presets"] = {}
        self.linked_widgets = {}
        self.presets_queue = LifoQueue()
        self.presets_update_queue = []
        self.isLoaded = False
        self.externalRegistries = {}

        self.initLayout()

    def loadConfig(self, config_file, defaults_file):
        """
        Import settings registry

        Parameters
        ==========
        config_file
            Settings registry config.json file
        defaults_file
            Default config file
        """
        common.app_manager.updateState(common.AppState.SettingsRegistryInit)
        self.conf = config.Config(
            config_file=config_file,
            default_config_file=defaults_file,
            disableSaving=True,
        )
        if not self.conf.loadConfig():
            os._exit(1)

        if self.conf.get("tabs") is not None:
            for i in range(len(self.conf["tabs"])):
                with open(
                    os.path.join(
                        self.basedir,
                        "settings_registry",
                        self.conf["tabs"][i]["config"],
                    ),
                    "r",
                ) as f:
                    self.conf["tabs"][i]["conf"] = json.load(f)

            for key, value in self.conf["external"].items():
                with open(
                    os.path.join(
                        self.basedir, "settings_registry", "external", key + ".json"
                    ),
                    "r",
                ) as f:
                    self.external_reg[key] = json.load(f)
                self.external_reg[key]["extra"] = self.conf["external"][key]

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
            key = name.split(".")[-1:][0]
            if hasattr(serial[name], "conf"):
                self.settings["serial"][key] = serial[name].conf
            else:
                self.logger.error("serialpipe." + key + " has no conf attribute")

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
        common.app_manager.updateState(common.AppState.SettingsHandlersInit)
        s_config = os.path.join(handlers_dir, "config.json")
        s_default = os.path.join(handlers_dir, "config_defaults.json")
        self.handlers_conf = config.Config(
            config_file=s_config, default_config_file=s_default, disableSaving=True
        )
        if not self.handlers_conf.loadConfig():
            self.logger.error("Missing " + s_config + " file")
            os._exit(1)

        self.handlers = {}
        for mod_name in self.handlers_conf["handlers_modules"]:
            handler = importlib.import_module(
                "smartwheel." + self.conf["settings_handlers_dir"] + "." + mod_name
            )
            h_dict = handler.handlers
            for k in h_dict:
                if self.handlers.get(k) is not None:
                    self.logger.warning(
                        "Setting handler " + k + " is defined twice. Overriding"
                    )
                self.handlers[k] = h_dict[k](
                    self.getValue, self.setValue, weakref.ref(self)
                )

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

        props = prop.split(".")
        cur_prop = self.settings[module]
        for p in props:
            if cur_prop.get(p) is None:
                self.logger.error(
                    "Could not get value: no property " + module + "." + prop
                )
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

        Returns True if new value is different

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
            key = "_" + str(_i - 1)

        # We create the wrapper if needed
        if d.get(key) is None:
            w = {key: d}
        else:
            w = d

        if len(props) == 1:
            if index is None:
                new = not w[key].get(props[0]) == value
                w[key][props[0]] = value
            elif type(index) == list:
                new = False
                for i in index:
                    new = new or (not w[key][props[0]][i] == value)
                    w[key][props[0]][i] = value
            else:
                new = not w[key][props[0]][index] == value
                w[key][props[0]][index] = value
            return new

        # Python reference hack, we use a mutable type as a wrapper
        wrapper = {"_" + str(_i): w[key][props[0]]}

        return self.dictWalk(wrapper, props[1:], value, index, _i + 1)

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

        props = prop.split(".")

        if self.dictWalk(self.settings[module], props, value, index):
            name = module + "." + prop
            if index is not None:
                name += "." + str(index)
            self.setCustom(name)

            if self.isLoaded:
                common.config_manager.updated.emit(props[-1:][0])
                self.main_class().update()
            else:
                self.presets_update_queue.append(props[-1:][0])

    def savePreset(self, index, name, title, filepath):
        """
        Save the specified preset

        Parameters
        ==========
        index
            Settings tab index
        name
            Preset internal name
        title
            Preset title
        filepath
            Path to the preset json file (may not exist)
        """
        preset = {"name": name, "title": title, "props": {}}

        for key, _ in self.preset_tabs[index].items():
            elem, handler = self.preset_tabs[index][key]
            prop = elem().property("preset_property")
            value = handler.fetchValue(elem())

            if value is None:
                continue

            preset["props"][prop] = value

        self.conf["presets"][str(index)][name] = preset

        with open(filepath, "w") as f:
            json.dump(preset, f, indent=4)

        return True, preset

    def loadPreset(self, index, name):
        """
        Load the preset from the handler

        Parameters
        ==========
        index
            Settings tab index
        name
            Preset internal name
        """
        if not self.isLoaded:
            self.presets_queue.put((index, name))
            return

        preset = self.conf["presets"][str(index)][name]

        for key, value in preset["props"].items():
            p_elem = self.preset_tabs[index].get(key)
            if p_elem is None:
                self.logger.warning(
                    "Could not find " + key + " widget from preset " + preset["title"]
                )
                continue

            elem, handler = p_elem

            ok = handler.updateValue(elem(), value)
            if not ok:
                self.logger.warning(
                    "Could not set "
                    + key
                    + " widget value from preset "
                    + preset["title"]
                )
            #else:
            #    self.presetValueSet.connect(self.preset_controllers[index]().setCustom)

    def setCustom(self, name):
        """
        Set custom preset on settings edit

        Parameters
        ==========
        name
            Internal preset name
        """
        index = self.presets_index_mapping.get(name)
        if index is None:
            return
        self.preset_controllers[index]().setCurrentText("Custom")

    @pyqtSlot(str)
    def showLinkedWidgets(self, text):
        """
        Show/hide linked widgets of the external registry selector. Intended to work with QComboBox

        Parameters
        ==========
        index
            Index of selected element
        """
        caller = self.sender()

        linked_to = caller.property("registriesName")

        if linked_to is None:
            self.logger.warning(
                "External registries widget does not have registries name"
            )

        self._showWidgets(linked_to, text)

    def _showWidgets(self, linked_to, text):
        for key, pair in self.linked_widgets[linked_to].items():
            for p in pair:
                if key == text:
                    p[0]().setRowVisible(p[1], True)
                else:
                    p[0]().setRowVisible(p[1], False)

    def processItem(self, elem, index, form, tab, registriesName=None):
        if elem.get("name") is not None:
            label = QLabel(elem["name"])
        else:
            label = None

        wid = None

        elem["tab_index"] = index  # storing the index of the current tab

        if self.handlers.get(elem["type"]) is None:
            self.logger.error(
                "Could not find the handler for type "
                + elem["type"]
                + " ("
                + elem["module"]
                + "."
                + elem["prop"]
                + ")"
            )
        else:
            wid = self.handlers[elem["type"]].initElem(elem)

        if wid is not None:
            prop_preset = ""

            if elem.get("module") is not None:
                wid.setProperty("widmodule", elem["module"])
                prop_preset += elem["module"]

            if elem.get("prop") is not None:
                wid.setProperty("prop", elem["prop"])
                prop_preset += "." + elem["prop"]

            if elem.get("index") is not None:
                wid.setProperty("index", elem["index"])
                prop_preset += "." + str(elem["index"])

            if elem["type"] == "preset":
                self.preset_controllers[index] = weakref.ref(wid.findChild(QComboBox))

            if (
                tab["conf"].get("enable_presets", False)
                and elem.get("preset", False)
                and not prop_preset == ""
            ):
                wid.setProperty("preset_property", prop_preset)

                self.preset_tabs[index][prop_preset] = (
                    weakref.ref(wid),
                    self.handlers[elem["type"]],
                )

                self.presets_index_mapping[prop_preset] = index

            if registriesName is not None:
                ok = self.handlers[elem["type"]].linkElem(wid, registriesName)
                if not ok:
                    self.logger.warning(
                        "Element type "
                        + elem["type"]
                        + " does not support linking extra registries"
                        + " ("
                        + elem["module"]
                        + "."
                        + elem["prop"]
                        + ")"
                    )

            widWrapper = QHBoxLayout()

            if label is not None:
                wid.setMinimumWidth(self.conf["fieldWidth"])
                wid.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                spacer = QSpacerItem(
                    40,
                    20,
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Minimum,
                )
                widWrapper.addSpacerItem(spacer)

            widWrapper.addWidget(wid)

            if label is not None:
                form.addRow(label, widWrapper)
            else:
                form.addRow(widWrapper)

        return form.rowCount() - 1, wid

    def initExtraRegistries(self):
        for reg, value in self.external_reg.items():
            if value.get("inPlace", False):
                continue

            scroll = QScrollArea()
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidgetResizable(True)
            wrapper = QWidget()
            wrapper.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
            form = QFormLayout()

            for elem in value["items"]:
                tab = {"conf": {"enable_presets": False}}
                index = None
                self.processItem(elem, index, form, tab)

            wrapper.setLayout(form)
            scroll.setWidget(wrapper)
            scroll.setWindowTitle("Settings")
            self.externalRegistries[reg] = scroll

    def initTab(self, index):
        """
        Parse registry and generate elements

        Parameters
        ==========
        index
            Tab index
        """
        tab = self.conf["tabs"][index]

        if tab["conf"].get("enable_presets", False):
            self.preset_tabs[index] = {}

        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout()
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        for elem_group in tab["conf"]["items"]:
            form = QFormLayout()
            group = QGroupBox(elem_group["name"])

            items = elem_group["options"]

            for i, elem in enumerate(items):
                if elem.get("external") is not None:
                    if type(elem["external"]) == dict:
                        ok, ex_registries = self.getValue(
                            module=elem["external"]["module"],
                            prop=elem["external"]["prop"],
                            index=elem["external"].get("index"),
                        )

                        if not ok:
                            self.logger.error(
                                "Could not find external registries in " + elem["name"]
                            )
                            continue

                        if not type(ex_registries) == list:
                            ex_registries = [ex_registries]
                    else:
                        ex_registries = elem["external"]

                    if elem["external"].get("pickerName") is None:
                        self.logger.error(
                            "No registry specified for element " + elem["name"]
                        )
                        continue

                    registries_name = elem["external"]["pickerName"]

                    _, controller = self.processItem(
                        elem, index, form, tab, registriesName=registries_name
                    )

                    self.linked_widgets[registries_name] = {}

                    for reg_name in ex_registries:
                        if self.external_reg.get(reg_name) is None:
                            self.logger.warning(
                                "No such external registry: " + reg_name
                            )
                            continue

                        exr = self.external_reg[reg_name]

                        if exr.get("items") is None:
                            self.logger.error(
                                "External registry " + reg_name + " does not have items"
                            )
                            continue

                        if not type(exr["items"]) == list:
                            self.logger.warning(
                                "External registry " + reg_name + " is not a list"
                            )
                            continue

                        self.linked_widgets[registries_name][
                            exr["extra"]["linkedCombo"]
                        ] = []

                        for reg in exr["items"]:
                            form_row, _ = self.processItem(reg, index, form, tab)
                            self.linked_widgets[registries_name][
                                exr["extra"]["linkedCombo"]
                            ].append((weakref.ref(form), form_row))

                        self._showWidgets(registries_name, controller.currentText())

                else:
                    self.processItem(elem, index, form, tab)

            group.setLayout(form)
            layout.addWidget(group)

        wrapper.setLayout(layout)
        scroll.setWidget(wrapper)

        return scroll

    def initLayout(self):
        """
        Generate layout
        """
        common.app_manager.updateState(common.AppState.SettingsInit)
        self.initExtraRegistries()

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
        spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        bottomPanel.addSpacerItem(spacer)
        bottomPanel.addWidget(cancelButton)
        bottomPanel.addWidget(applyButton)
        bottomPanel.addWidget(okButton)

        baseLayout.addLayout(bottomPanel)

        self.setLayout(baseLayout)

        self.isLoaded = True

        while not self.presets_queue.empty():
            self.loadPreset(*self.presets_queue.get())

        # updating properties
        if not self.presets_update_queue == []:
            common.config_manager.batchUpdate.emit(self.presets_update_queue)
            self.main_class().update()

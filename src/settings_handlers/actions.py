from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QGridLayout, QCheckBox, QGroupBox
from PyQt5.QtGui import QFont
from .base import BaseHandler
import logging

class ActionPicker(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ActionPicker, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)
        self.pickers = [] # Prevent pickers from being destroyed

    def initElem(self, elem):
        """
        Initialize actions picker, should not be called directly from settings.py

        Parameters
        ==========
        elem
            Action engine command {"name": "commandTitle", "device": "commandBind", "command": "commandName"}
        """
        wrapper = QWidget()
        wid = QHBoxLayout()
        sp = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        label = QLabel(elem["name"])
        editButton = QPushButton("...")
        deleteButton = QPushButton("x")
        
        # Fetching the ActionList
        if self.parent_obj is None:
            self.logger.error("Could not get settings object")
            return None

        picker = self.parent_obj().handlers["actions_list"].initElem(elem)
        if picker is None:
            self.logger.error("Could not initialize actions window")
            return None

        self.pickers.append(picker)

        editButton.clicked.connect(picker.show)

        wid.addWidget(label)
        wid.addSpacerItem(sp)
        wid.addWidget(editButton)
        wid.addWidget(deleteButton)
        
        wrapper.setLayout(wid)

        return wrapper


class ActionList(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ActionList, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        """
        Initialize actions picker window, should not be called directly from settings.py

        Parameters
        ==========
        elem
            Action engine command name {"device": "commandBind", "command": "commandName"}
        """
        #if parent_obj is None:
        #    self.logger.error("Could not load action editor: no parent object found")
        #    return None
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QVBoxLayout()

        wheel_l = QGridLayout()
        module_l = QGridLayout()

        wheel = QGroupBox("Wheel actions")
        module = QGroupBox("Module actions")

        ok, actions = self.value_getter("actionengine", "commandActions")
        
        if not ok:
            self.logger.error("Could not get actionengine config")
            return None

        if elem.get("device") is None or elem.get("command") is None:
            self.logger.error("No command bind specified, could not launch action editor")
            return None

        # {"command": "commandName", "actions": [{"action": "...", "mode": "...", "repeat": ..}, ...]}
        ok, elem_bind = self.value_getter("actionengine", "commandBind." + elem["device"])
        if not ok:
            elem_bind = []

        elem_actions = []
        for e in elem_bind:
            if e.get("command") is not None and e["command"] == elem["command"]:
                elem_actions = e.get("actions", [])

        font = QFont()
        font.setBold(True)

        wheel_l.setColumnStretch(10, 0)
        module_l.setColumnStretch(10, 0)

        for group in ["wheel", "module"]:
            enabled_label = QLabel("Enabled")
            title_label = QLabel("Title")
            any_label = QLabel("Call in any mode")
            
            if group == "wheel":
                desc_label = QLabel("Description")
                desc_label.setFont(font)
                module_label = QLabel("Call in module mode")
                module_label.setFont(font)
            else:
                wheel_label = QLabel("Call in wheel mode")
                wheel_label.setFont(font)

            enabled_label.setFont(font)
            title_label.setFont(font)
            any_label.setFont(font)

            if group == "wheel":
                wheel_l.addWidget(enabled_label, 0, 0, Qt.AlignLeft)
                wheel_l.addWidget(title_label, 0, 1, Qt.AlignLeft)
                wheel_l.addWidget(desc_label, 0, 2, Qt.AlignLeft)
                wheel_l.addWidget(any_label, 0, 3, Qt.AlignLeft)
                wheel_l.addWidget(module_label, 0, 4, Qt.AlignLeft)

            if group == "module":
                module_l.addWidget(enabled_label, 0, 0, Qt.AlignLeft)
                module_l.addWidget(title_label, 0, 1, Qt.AlignLeft)
                module_l.addWidget(any_label, 0, 2, Qt.AlignLeft)
                module_l.addWidget(wheel_label, 0, 3, Qt.AlignLeft)

        for i, a in enumerate(actions):
            enabled = QCheckBox()
            if a.get("title") is not None:
                title = QLabel(a["title"])
                desc = QLabel(a["description"])
            else:
                title = QLabel(a["description"])
                desc = None #QLabel("...")

            anyState = QCheckBox()

            if a["type"] == "wheel":
                activateInModule = QCheckBox()
                anyState.clicked.connect(activateInModule.setDisabled)
                anyState.clicked.connect(activateInModule.setChecked)
            else:
                activateInWheel = QCheckBox()
                anyState.clicked.connect(activateInWheel.setDisabled)
                anyState.clicked.connect(activateInWheel.setChecked)

            if a.get("default") is not None:
                if a["default"] == "any":
                    anyState.click() # unchecked by deafult
                elif a["default"] == "wheel":
                    if bind["mode"] == "module":
                        activateInWheel.click()
                elif a["default"] == "module":
                    if bind["mode"] == "wheel":
                        activateInModule.click()

            for j, bind in enumerate(elem_actions):
                if bind["action"] == a["name"]:
                    enabled.setChecked(True)
                else:
                    continue
                
                if a["type"] == "wheel":
                    if bind["mode"] == "wheel":
                        activateInModule.setChecked(False)
                    else:
                        activateInModule.setChecked(True)
                if a["type"] == "module":
                    if bind["mode"] == "module":
                        activateInWheel.setChecked(False)
                    else:
                        activateInWheel.setChecked(True)   

                if not bind["checkState"]:
                    if not anyState.isChecked():
                        anyState.click()

            if a["type"] == "wheel":
                wheel_l.addWidget(enabled, i+1, 0, Qt.AlignLeft)
                wheel_l.addWidget(title, i+1, 1, Qt.AlignLeft)
                if desc is not None:
                    wheel_l.addWidget(desc, i+1, 2, Qt.AlignLeft)
                wheel_l.addWidget(anyState, i+1, 3, Qt.AlignLeft)
                wheel_l.addWidget(activateInModule, i+1, 4, Qt.AlignLeft)

                for j in range(1, 5):
                    enabled.clicked.connect(wheel_l.itemAtPosition(i+1, j).widget().setEnabled)
                    if not enabled.isChecked():
                        wheel_l.itemAtPosition(i+1, j).widget().setDisabled(True)
            else:
                module_l.addWidget(enabled, i+1, 0, Qt.AlignLeft)
                module_l.addWidget(title, i+1, 1, Qt.AlignLeft)
                module_l.addWidget(anyState, i+1, 2, Qt.AlignLeft)
                module_l.addWidget(activateInWheel, i+1, 3, Qt.AlignLeft)

                for j in range(1, 4):
                    enabled.clicked.connect(module_l.itemAtPosition(i+1, j).widget().setEnabled)
                    if not enabled.isChecked():
                        module_l.itemAtPosition(i+1, j).widget().setDisabled(True)


        panel = QHBoxLayout()
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        panel.addSpacerItem(spacer)
        panel.addWidget(cancelButton)
        panel.addWidget(okButton)

        wheel.setLayout(wheel_l)
        module.setLayout(module_l)

        layout.addWidget(wheel)
        layout.addWidget(module)
        layout.addLayout(panel)

        wrapper.setLayout(layout)

        wrapper.setWindowTitle("Edit actions")

        return wrapper


handlers = {"actions_picker": ActionPicker, "actions_list": ActionList}

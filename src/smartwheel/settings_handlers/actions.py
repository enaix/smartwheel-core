import logging

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from smartwheel.settings_handlers.base import BaseHandler


class ActionPicker(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ActionPicker, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)
        self.pickers = []  # Prevent pickers from being destroyed

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
        sp = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
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


class OnShown(QWidget):
    """
    Widget that calls the shown signal when visible
    Qt has no proper way to have 2 gridlayouts with the same column size, so I had to implement this hack
    """

    shown = pyqtSignal()

    def showEvent(self, event):
        self.shown.emit()
        event.accept()


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
        # if parent_obj is None:
        #    self.logger.error("Could not load action editor: no parent object found")
        #    return None
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
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
            self.logger.error(
                "No command bind specified, could not launch action editor"
            )
            return None

        # {"command": "commandName", "actions": [{"action": "...", "mode": "...", "repeat": ..}, ...]}
        ok, elem_bind = self.value_getter(
            "actionengine", "commandBind." + elem["device"]
        )
        if not ok:
            elem_bind = []

        elem_actions = []
        for e in elem_bind:
            if e.get("command") is not None and e["command"] == elem["command"]:
                elem_actions = e.get("actions", [])

        font = QFont()
        font.setBold(True)

        for i, s in enumerate([10, 0, 0, 0]):
            wheel_l.setColumnStretch(s, i)
            module_l.setColumnStretch(s, i)

        for group in ["wheel", "module"]:
            enabled_label = QLabel("Enabled")
            title_label = QLabel("Title")
            any_label = QLabel("Where to call")

            desc_label = QLabel("Description")
            desc_label.setFont(font)

            enabled_label.setFont(font)
            title_label.setFont(font)
            any_label.setFont(font)

            if group == "wheel":
                wheel_l.addWidget(enabled_label, 0, 0, Qt.AlignmentFlag.AlignLeft)
                wheel_l.addWidget(title_label, 0, 1, Qt.AlignmentFlag.AlignLeft)
                wheel_l.addWidget(desc_label, 0, 2, Qt.AlignmentFlag.AlignLeft)
                wheel_l.addWidget(any_label, 0, 3, Qt.AlignmentFlag.AlignLeft)

            if group == "module":
                module_l.addWidget(enabled_label, 0, 0, Qt.AlignmentFlag.AlignLeft)
                module_l.addWidget(title_label, 0, 1, Qt.AlignmentFlag.AlignLeft)
                module_l.addWidget(desc_label, 0, 2, Qt.AlignmentFlag.AlignLeft)
                module_l.addWidget(any_label, 0, 3, Qt.AlignmentFlag.AlignLeft)

        for i, a in enumerate(actions):
            enabled = QCheckBox()

            enabled.setProperty("action_name", a["name"])

            title = QLabel(a["title"])
            desc = QLabel(a["description"])

            state = QComboBox()
            state.insertItems(0, ["Wheel", "Module", "Anywhere"])
            # anyState = QCheckBox()

            if a.get("default") is not None:
                if a["default"] == "any":
                    state.setCurrentIndex(2)
                elif a["default"] == "wheel":
                    if bind["mode"] == "module":
                        state.setCurrentIndex(1)
                    else:
                        state.setCurrentIndex(0)
                elif a["default"] == "module":
                    if bind["mode"] == "wheel":
                        state.setCurrentIndex(0)
                    else:
                        state.setCurrentIndex(1)

            for j, bind in enumerate(elem_actions):
                if bind["action"] == a["name"]:
                    enabled.setChecked(True)
                else:
                    continue

                if a["type"] == "wheel":
                    if bind.get("onState") is not None and bind["onState"] == "module":
                        state.setCurrentIndex(1)
                    else:
                        state.setCurrentIndex(0)
                if a["type"] == "module":
                    if bind.get("onState") is not None and bind["onState"] == "wheel":
                        state.setCurrentIndex(0)
                    else:
                        state.setCurrentIndex(1)

                if not bind["checkState"]:
                    state.setCurrentIndex(2)

            if a["type"] == "wheel":
                wheel_l.addWidget(enabled, i + 1, 0, Qt.AlignmentFlag.AlignLeft)
                wheel_l.addWidget(title, i + 1, 1, Qt.AlignmentFlag.AlignLeft)
                wheel_l.addWidget(desc, i + 1, 2, Qt.AlignmentFlag.AlignLeft)
                wheel_l.addWidget(state, i + 1, 3, Qt.AlignmentFlag.AlignRight)

                for j in range(1, 4):
                    if wheel_l.itemAtPosition(i + 1, j) is not None:
                        enabled.clicked.connect(
                            wheel_l.itemAtPosition(i + 1, j).widget().setEnabled
                        )
                        if not enabled.isChecked():
                            wheel_l.itemAtPosition(i + 1, j).widget().setDisabled(True)
            else:
                module_l.addWidget(enabled, i + 1, 0, Qt.AlignmentFlag.AlignLeft)
                module_l.addWidget(title, i + 1, 1, Qt.AlignmentFlag.AlignLeft)
                module_l.addWidget(desc, i + 1, 2, Qt.AlignmentFlag.AlignLeft)
                module_l.addWidget(state, i + 1, 3, Qt.AlignmentFlag.AlignRight)

                for j in range(1, 4):
                    enabled.clicked.connect(
                        module_l.itemAtPosition(i + 1, j).widget().setEnabled
                    )
                    if not enabled.isChecked():
                        module_l.itemAtPosition(i + 1, j).widget().setDisabled(True)

        panel = QHBoxLayout()
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.applyChanges)
        okButton.clicked.connect(wrapper.close)

        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(wrapper.close)

        onShown = OnShown()
        onShown.shown.connect(self.resizeCells)
        panel.addWidget(onShown)

        spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
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

        okButton.setProperty("wrapper", wrapper)
        okButton.setProperty("elem", elem)
        onShown.setProperty("wrapper", wrapper)

        return wrapper

    @pyqtSlot()
    def resizeCells(self):
        caller = self.sender()
        wrapper = caller.property("wrapper")

        wheel_l = (
            wrapper.findChild(QVBoxLayout).itemAt(0).widget().findChild(QGridLayout)
        )
        module_l = (
            wrapper.findChild(QVBoxLayout).itemAt(1).widget().findChild(QGridLayout)
        )

        title_width = max([l.cellRect(0, 1).width() for l in [wheel_l, module_l]])
        wheel_l.setColumnMinimumWidth(1, title_width)
        module_l.setColumnMinimumWidth(1, title_width)

    @pyqtSlot()
    def applyChanges(self):
        caller = self.sender()
        wrapper = caller.property("wrapper")
        elem = caller.property("elem")

        if wrapper is None or elem is None:
            self.logger.error("Could not get apply button propery")
            return

        actions = []

        for i, group in enumerate(
            [wrapper.findChild(QVBoxLayout).itemAt(x).widget() for x in [0, 1]]
        ):
            grid = group.findChild(QGridLayout)

            for j in range(1, grid.rowCount()):
                enabled_button = grid.itemAtPosition(j, 0)
                if enabled_button is None:
                    continue

                enabled = enabled_button.widget().isChecked()
                if not enabled:
                    continue

                onState = grid.itemAtPosition(j, 3).widget().currentText().lower()
                if i == 0:  # wheel
                    mode = "wheel"

                if i == 1:  # module
                    mode = "module"

                anyState = False
                if onState == "anywhere":
                    anyState = True

                actionName = grid.itemAtPosition(j, 0).widget().property("action_name")

                action = {
                    "action": actionName,
                    "mode": mode,
                    "checkState": not anyState,
                }

                if not anyState and not mode == onState:
                    action["onState"] = onState

                actions.append(action)

        # Saving
        exists, elem_bind = self.value_getter(
            "actionengine", "commandBind." + elem["device"]
        )
        if not exists:
            elem_bind = [{"command": elem["command"], "actions": []}]

        found = False
        for i, e in enumerate(elem_bind):
            if e.get("command") is not None and e["command"] == elem["command"]:
                found = True
                elem_bind[i]["actions"] = actions

        if not found:
            elem_bind.append({"command": elem["command"], "actions": actions})

        self.value_setter(
            module="actionengine", prop="commandBind." + elem["device"], value=elem_bind
        )


handlers = {"actions_picker": ActionPicker, "actions_list": ActionList}

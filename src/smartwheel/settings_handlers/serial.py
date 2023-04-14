import logging

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from smartwheel.settings_handlers.base import BaseHandler


class SerialHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(SerialHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)
        self.pickers = []

    def initElem(self, elem):
        ok, binds = self.value_getter(module=elem["module"], prop=elem["prop"])
        if not ok:
            self.logger.warning("Could not get serial handler binds")
            return None

        lwid = self.parent_obj().handlers["listmanager"].initElem({"binds": binds})
        lwid.setProperty("module", elem["module"])
        lwid.setProperty("prop", elem["prop"])
        lwid.newCommand.connect(self.newCommand)
        lwid.delCommand.connect(self.delCommand)
        lwid.newGroup.connect(self.newGroup)
        lwid.delGroup.connect(self.delGroup)
        lwid.editCommandName.connect(self.editCommandName)
        lwid.editCommandProps.connect(self.editCommandProps)
        return lwid

    @pyqtSlot(QWidget)
    def newCommand(self, wid):
        caller = self.sender()
        group = wid.property("linkedGroup")
        base = wid.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not get ListBox widget")
            return

        module = base().property("module")
        prop = base().property("prop")

        if group is None or group() is None:
            self.logger.warning("Could not get command group widget")
            return

        name = group().title()

        ok, binds = self.value_getter(module=module, prop=prop)
        if not ok:
            self.logger.warning("Could not get serial binds")
            return

        for i in range(len(binds)):
            if binds[i]["name"] == name:
                binds[i]["commands"].append({"string": ""})
                self.value_setter(module=module, prop=prop, value=binds)
                return

        self.logger.warning("Could not get group with name " + name)
        return

    @pyqtSlot(QWidget)
    def delCommand(self, wid):
        caller = self.sender()
        group = wid.property("linkedGroup")
        base = wid.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not get ListBox widget")
            return

        module = base().property("module")
        prop = base().property("prop")

        if group is None or group() is None:
            self.logger.warning("Could not get command group widget")
            return

        name = group().title()

        ok, binds = self.value_getter(module=module, prop=prop)
        if not ok:
            self.logger.warning("Could not get serial binds")
            return

        cmd_name = wid.property("linkedLabel")().text()

        for i in range(len(binds)):
            if binds[i]["name"] == name:
                for j in range(len(binds[i]["commands"])):
                    if binds[i]["commands"][j]["string"] == cmd_name:
                        binds[i]["commands"].pop(j)
                        self.value_setter(module=module, prop=prop, value=binds)
                        return

        self.logger.warning("Could not get command with name " + cmd_name)
        return

    @pyqtSlot(QWidget)
    def editCommandName(self, wid):
        caller = self.sender()
        group = wid.property("linkedGroup")
        base = wid.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not get ListBox widget")
            return

        module = base().property("module")
        prop = base().property("prop")

        if group is None or group() is None:
            self.logger.warning("Could not get command group widget")
            return

        name = group().title()

        ok, binds = self.value_getter(module=module, prop=prop)
        if not ok:
            self.logger.warning("Could not get serial binds")
            return

        newText = wid.property("linkedLabel")().text()
        oldText = wid.property("linkedLabel")().property("oldText")

        for i in range(len(binds)):
            if binds[i]["name"] == name:
                for j in range(len(binds[i]["commands"])):
                    if binds[i]["commands"][j]["string"] == oldText:
                        binds[i]["commands"][j]["string"] = newText
                        self.value_setter(module=module, prop=prop, value=binds)
                        wid.property("linkedLabel")().setProperty("oldText", newText)
                        return

        self.logger.warning("Could not get command with name " + cmd_name)
        return

    @pyqtSlot(QWidget)
    def editCommandProps(self, wid):
        caller = self.sender()
        group = wid.property("linkedGroup")
        base = wid.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not get ListBox widget")
            return

        module = base().property("module")
        prop = base().property("prop")

        if group is None or group() is None:
            self.logger.warning("Could not get command group widget")
            return

        name = group().title()

        cmd_name = wid.property("linkedLabel")().text()

        context = {"device": name, "command": cmd_name}

        picker = self.parent_obj().handlers["actions_list"].initElem(context)
        self.pickers.append(picker)
        picker.show()

    @pyqtSlot(QGroupBox)
    def newGroup(self, wid):
        caller = self.sender()
        base = wid.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not get ListBox widget")
            return

        module = base().property("module")
        prop = base().property("prop")

        if module is None or prop is None:
            self.logger.warning("Could not get ListBox properties")
            return

        name = wid.title()

        item, ok = QInputDialog().getItem(
            caller, "Device type", "Device:", ["button", "encoder"], 0, False
        )
        if not ok:
            # closeButton = base().findChild(QVBoxLayout).findChild(QHBoxLayout).findChildren(QPushButton)
            # closeButton[1].clicked.emit()
            return

        ok, groups = self.value_getter(module=module, prop=prop)
        if not ok:
            self.logger.warning("Could not get serial binds")
            return

        groups.append({"name": name, "type": item, "commands": []})
        self.value_setter(module=module, prop=prop, value=groups)

    @pyqtSlot(QGroupBox)
    def delGroup(self, wid):
        caller = self.sender()
        base = wid.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not get ListBox widget")
            return

        module = base().property("module")
        prop = base().property("prop")

        if module is None or prop is None:
            self.logger.warning("Could not get ListBox properties")
            return

        name = wid.title()

        ok, groups = self.value_getter(module=module, prop=prop)
        if not ok:
            self.logger.warning("Could not get serial binds")
            return

        for i in range(len(groups)):
            if groups[i]["name"] == name:
                groups.pop(i)
                self.value_setter(module=module, prop=prop, value=groups)
                return

        self.logger.warning("Could not get group with name" + name)


handlers = {"serialmodule": SerialHandler}

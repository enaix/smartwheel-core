import logging

from PyQt6.QtWidgets import QListView, QInputDialog, QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSlot

from smartwheel.settings_handlers.base import BaseHandler


class SerialHandler(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(SerialHandler, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        ok, binds = self.value_getter(module=elem["module"], prop=elem["prop"])
        if not ok:
            self.logger.warning("Could not get serial handler binds")
            return None

        lwid = self.parent_obj().handlers["listmanager"].initElem({"binds": binds})
        lwid.setProperty("module", elem["module"])
        lwid.setProperty("prop", elem["prop"])
        lwid.newCommand.connect(self.newCommand)
        lwid.newGroup.connect(self.newGroup)
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

        #if not hasattr(group, "title"):
        #    self.logger.warning("Could not get group title")
        #    return

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

        item, ok = QInputDialog().getItem(caller, "Device type", "Device:", ["button", "encoder"], 0, False)
        if not ok:
            #closeButton = base().findChild(QVBoxLayout).findChild(QHBoxLayout).findChildren(QPushButton)
            #closeButton[1].clicked.emit()
            return

        ok, groups = self.value_getter(module=module, prop=prop)
        if not ok:
            self.logger.warning("Could not get serial binds")
            return

        groups.append({"name": name, "type": item, "commands": []})
        self.value_setter(module=module, prop=prop, value=groups)



handlers = {"serialmodule": SerialHandler}

import logging

from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
)
import weakref

from smartwheel.settings_handlers.base import BaseHandler


class ModulesLoader(BaseHandler):
    """
    Common modules picker
    """

    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ModulesLoader, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        """
        Initialize modules picker, should not be called directly from settings.py

        Parameters
        ==========
        elem
            Dict containing modules {"modules": [{"name": "internalName", "title": ..., "description": ...,}, ...], "modulesLoad": [0, 1, ...]}
        """
        layout = QGridLayout()

        font = QFont()
        font.setBold(True)

        labels = [QLabel(x) for x in ["Enabled", "Title", "Description", "Options"]]

        for i in range(len(labels)):
            labels[i].setFont(font)
            layout.addWidget(labels[i], 0, i, Qt.AlignmentFlag.AlignLeft)

        # layout.setColumnStretch(10, 0)

        for i, mod in enumerate(elem["modules"]):
            check = QCheckBox()
            options = QPushButton("...")

            lwid = self.parent_obj().handlers["listmanager"].initElem(elem)
            options.clicked.connect(lwid.show)

            check.setProperty("name", mod["name"])

            if i in elem["modulesLoad"]:
                check.setChecked(True)

            for j, s in enumerate(["title", "description"]):
                label = QLabel(mod[s])

                layout.addWidget(label, i + 1, j + 1, Qt.AlignmentFlag.AlignLeft)

            layout.addWidget(check, i + 1, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(options, i + 1, 3, Qt.AlignmentFlag.AlignLeft)

            for j in range(1, 4):
                if layout.itemAtPosition(i + 1, j) is not None:
                    check.clicked.connect(
                        layout.itemAtPosition(i + 1, j).widget().setEnabled
                    )
                    if not check.isChecked():
                        layout.itemAtPosition(i + 1, j).widget().setDisabled(True)

        vbox = QVBoxLayout()
        vbox.addLayout(layout)

        spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        vbox.addSpacerItem(spacer)

        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        wrapper.setLayout(vbox)

        return wrapper


class SerialLoader(BaseHandler):
    """
    Serial modules picker
    """

    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(SerialLoader, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)

    def initElem(self, elem):
        """
        Load serial modules picker

        Parameters
        ==========
        elem
            Element from config
        """
        ok, modules = self.value_getter("canvas", "serialModules")
        if not ok:
            self.logger.error("Could not get serial modules")
            return None

        ok, modulesLoad = self.value_getter("canvas", "serialModulesLoad")
        if not ok:
            self.logger.error("Could not get loaded serial modules")
            return None

        elem["modules"] = modules
        elem["modulesLoad"] = modulesLoad

        picker = self.parent_obj().handlers["modules"].initElem(elem)
        if picker is None:
            self.logger.error("Could not initialize modules picker")
            return None

        layout = picker.findChild(QVBoxLayout).findChild(QGridLayout)

        for i in range(1, layout.rowCount()):
            if layout.itemAtPosition(i, 0) is None:
                break

            checked = layout.itemAtPosition(i, 0).widget()
            checked.clicked.connect(self.setEnabled)

        return picker

    @pyqtSlot(bool)
    def setEnabled(self, enabled):
        caller = self.sender()

        name = caller.property("name")

        ok, modules = self.value_getter("canvas", "serialModules")
        if not ok:
            self.logger.error("Could not get serial modules")
            return

        ok, modulesLoad = self.value_getter("canvas", "serialModulesLoad")
        if not ok:
            self.logger.error("Could not get loaded serial modules")
            return

        index = None
        for i in range(len(modules)):
            if modules[i]["name"] == name:
                index = i
                break

        if index is None:
            self.logger.error("Could not get module by name")
            return

        if enabled:
            m_set = set(modulesLoad)
            m_set.add(index)
            modulesLoad = list(m_set)
        else:
            modulesLoad.remove(index)

        self.value_setter(module="canvas", prop="serialModulesLoad", value=modulesLoad)


class ListBox(QWidget):
    newCommand = pyqtSignal(QWidget)
    delCommand = pyqtSignal(QWidget)
    newGroup = pyqtSignal(QGroupBox)
    delGroup = pyqtSignal(QGroupBox)
    editCommandProps = pyqtSignal(QWidget)
    editCommandName = pyqtSignal(QWidget)

    def __init__(self, *args, **kwargs):
        super(ListBox, self).__init__(*args, **kwargs)


class ListViewManager(BaseHandler):
    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ListViewManager, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)
        self.elems = []

    def initElem(self, elem):
        wrapper = ListBox()
        layout = QVBoxLayout()
        baseLayout = QVBoxLayout()
        buttons = QHBoxLayout()
        addButton = QPushButton("+")

        addButton.setProperty("linkedWidget", weakref.ref(wrapper))
        addButton.clicked.connect(self.appendGroup)

        buttons.addWidget(addButton)
        layout.addLayout(baseLayout)
        layout.addLayout(buttons)
        wrapper.setLayout(layout)

        #self.addGroup(baseLayout)
        #self.addGroup(baseLayout)
        self.elems.append(wrapper)

        return wrapper

    def addCommand(self, listWid, baseWidget):
        wrapper = QWidget()
        listItem = QListWidgetItem()
        label = QLineEdit()
        layout = QHBoxLayout()
        confButton = QPushButton("...")
        delButton = QPushButton("x")

        delButton.setProperty("linkedItem", weakref.ref(listItem))
        delButton.setProperty("linkedList", weakref.ref(listWid))
        delButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        confButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        label.setProperty("linkedWidget", weakref.ref(baseWidget))

        delButton.clicked.connect(self.delCommand)

        layout.addWidget(label)
        layout.addWidget(confButton)
        layout.addWidget(delButton)
        wrapper.setLayout(layout)
        listItem.setSizeHint(wrapper.sizeHint())
        listWid.addItem(listItem)
        listWid.setItemWidget(listItem, wrapper)
        baseWidget.newCommand.emit(wrapper)
    
    @pyqtSlot()
    def delCommand(self):
        caller = self.sender()
        item = caller.property("linkedItem")
        wid = caller.property("linkedList")
        base = caller.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        if item is None or wid is None or item() is None or wid() is None:
            self.logger.warning("Could not find linked QListWidget")
            return

        base().delCommand.emit(wid().itemWidget(item()))
        wid().takeItem(wid().row(item()))

    @pyqtSlot()
    def appendCommand(self):
        caller = self.sender()
        wid = caller.property("linkedList")
        base = caller.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        if wid is None or wid() is None:
            self.logger.warning("Could not find linked QListWidget")
            return
        
        self.addCommand(wid(), base())

    @pyqtSlot()
    def appendGroup(self):
        caller = self.sender()
        base = caller.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        self.addGroup(base())

    def addGroup(self, baseWidget):
        baseLayout = baseWidget.findChild(QVBoxLayout)
        if baseLayout is None:
            self.logger.warning("Could not find base layout of the listbox")
            return

        group = QGroupBox("Button")
        layout = QVBoxLayout()
        listWid = QListWidget()
        buttons = QHBoxLayout()
        addButton = QPushButton("Add command")
        delButton = QPushButton("x")
        addButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        delButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        delButton.setProperty("linkedGroup", weakref.ref(group))
        delButton.setProperty("linkedLayout", weakref.ref(baseLayout))

        addButton.setProperty("linkedList", weakref.ref(listWid))
        addButton.clicked.connect(self.appendCommand)
        delButton.clicked.connect(self.removeGroup)

        buttons.addWidget(addButton)
        buttons.addWidget(delButton)
        layout.addWidget(listWid)
        layout.addLayout(buttons)
        group.setLayout(layout)
        baseLayout.addWidget(group)

        baseWidget.newGroup.emit(group)

        #self.addCommand(listWid)

    @pyqtSlot()
    def removeGroup(self):
        caller = self.sender()
        wid = caller.property("linkedGroup")
        base = caller.property("linkedWidget")
        layout = caller.property("linkedLayout")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        if wid is None or wid() is None or layout is None or layout() is None:
            self.logger.warning("Could not find linked group")
            return

        self.delGroup(wid(), layout(), base())

    def delGroup(self, group, layout, baseWidget):
        layout.removeWidget(group)
        baseWidget.delGroup.emit(group)


handlers = {"modules": ModulesLoader, "serial": SerialLoader, "listmanager": ListViewManager}

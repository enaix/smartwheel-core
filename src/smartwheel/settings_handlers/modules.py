import logging
import weakref

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

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
            Dict containing modules {"modules": [{"name": "internalName", "title": ..., "description": ...,}, ...], "modulesLoad": [0, 1, ...], "disabled": [0, ...]}
            Optional: module may contain registry property, which will be linked to the settings button
        """
        layout = QGridLayout()

        font = QFont()
        font.setBold(True)

        labels = [QLabel(x) for x in ["Enabled", "Title", "Description", "Options"]]

        for i in range(len(labels)):
            labels[i].setFont(font)
            layout.addWidget(labels[i], 0, i, Qt.AlignmentFlag.AlignLeft)

        # layout.setColumnStretch(10, 0)
        if elem.get("disabled") is not None:
            for i in elem["disabled"]:
                elem["modules"][i]["disabled"] = True

        for i, mod in enumerate(elem["modules"]):
            check = QCheckBox()
            options = QPushButton("...")

            if mod.get("registry") is not None:
                form = self.parent_obj().externalRegistries.get(mod["registry"])
                if form is not None:
                    options.clicked.connect(form.show)
                # handler = self.parent_obj().handlers.get(mod["handler"])
                # if handler is not None:
                # module_edit = handler.initElem(mod)
                # self.modules.append(module_edit)
                # options.clicked.connect(module_edit.show)

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
                    if mod.get("disabled", False):
                        layout.itemAtPosition(i + 1, j).widget().setDisabled(True)
                        layout.itemAtPosition(i + 1, 0).widget().setDisabled(True)
                    else:
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
    """
    List manager widget, emits various signals
    """

    newCommand = pyqtSignal(QWidget)
    delCommand = pyqtSignal(QWidget)
    newGroup = pyqtSignal(QGroupBox)
    delGroup = pyqtSignal(QGroupBox)
    editCommandProps = pyqtSignal(QWidget)
    editCommandName = pyqtSignal(QWidget)

    def __init__(self, *args, **kwargs):
        super(ListBox, self).__init__(*args, **kwargs)


class ListViewManager(BaseHandler):
    """
    Common list widget manager, useful for dynamically adding/removing elements in groups
    """

    def __init__(self, value_getter, value_setter, parent_obj=None):
        super(ListViewManager, self).__init__(value_getter, value_setter, parent_obj)
        self.logger = logging.getLogger(__name__)
        self.elems = []

    def initElem(self, elem):
        """
        Initialize list managet widget

        Elem must be in format `{"binds": {"name": "...", "commands": {"string": "...", ...}, ...}}`

        Parameters
        ==========
        elem
            Dictionary with elements content
        """
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

        for e in elem.get("binds", []):
            self.addGroup(wrapper, elem=e)

        self.elems.append(wrapper)

        return wrapper

    def addCommand(self, listWid, baseWidget, elem=None):
        """
        Create new list widget element and emit newCommand signal

        Parameters
        ==========
        listWid
            QListWidget object
        baseWidget
            Main ListBox object
        elem
            (Optional) Set element during init
        """
        wrapper = QWidget()
        listItem = QListWidgetItem()

        if elem is None:
            label = QLineEdit()
        else:
            label = QLineEdit(elem["string"])
        layout = QHBoxLayout()
        confButton = QPushButton("...")
        delButton = QPushButton("x")

        wrapper.setProperty("linkedWidget", weakref.ref(baseWidget))
        wrapper.setProperty("linkedLabel", weakref.ref(label))
        delButton.setProperty("linkedItem", weakref.ref(listItem))
        delButton.setProperty("linkedList", weakref.ref(listWid))
        delButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        confButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        confButton.setProperty("linkedItem", weakref.ref(wrapper))
        label.setProperty("linkedWidget", weakref.ref(baseWidget))
        label.setProperty("linkedItem", weakref.ref(wrapper))
        label.setProperty("oldText", label.text())
        wrapper.setProperty("linkedGroup", weakref.ref(listWid.parent()))

        delButton.clicked.connect(self.delCommand)
        confButton.clicked.connect(self.confCommand)
        label.editingFinished.connect(self.nameCommand)

        layout.addWidget(label)
        layout.addWidget(confButton)
        layout.addWidget(delButton)
        wrapper.setLayout(layout)
        listItem.setSizeHint(wrapper.sizeHint())
        listWid.addItem(listItem)
        listWid.setItemWidget(listItem, wrapper)
        baseWidget.newCommand.emit(wrapper)

    @pyqtSlot()
    def nameCommand(self):
        """
        Emit editCommandName signal on item edit
        """
        caller = self.sender()
        item = caller.property("linkedItem")
        base = caller.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        if item is None or item() is None:
            self.logger.warning("Could not find linked QListWidget")
            return

        base().editCommandName.emit(item())

    @pyqtSlot()
    def confCommand(self):
        """
        Emit editCommandProps signal on button press
        """
        caller = self.sender()
        item = caller.property("linkedItem")
        base = caller.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        if item is None or item() is None:
            self.logger.warning("Could not find linked QListWidget")
            return

        base().editCommandProps.emit(item())

    @pyqtSlot()
    def delCommand(self):
        """
        Delete command on delete button press and emit delCommand signal
        """
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
        """
        Add new command on button press
        """
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
        """
        Create new group on button press
        """
        caller = self.sender()
        base = caller.property("linkedWidget")

        if base is None or base() is None:
            self.logger.warning("Could not find base widget")
            return

        self.addGroup(base())

    def addGroup(self, baseWidget, elem=None):
        """
        Add new group and emit newGroup signal

        Parameters
        ==========
        baseWidget
            Base ListBox widget
        elem
            (Optional) Set element during init
        """
        baseLayout = baseWidget.findChild(QVBoxLayout)
        if baseLayout is None:
            self.logger.warning("Could not find base layout of the listbox")
            return

        if elem is None:
            name, ok = QInputDialog().getText(
                baseWidget,
                "New group",
                "Group name:",
                QLineEdit.EchoMode.Normal,
                "Group " + str(baseLayout.count() - 1),
            )
            if not ok:
                return
        else:
            name = elem["name"]

        group = QGroupBox(name)
        layout = QVBoxLayout()
        listWid = QListWidget()
        buttons = QHBoxLayout()
        addButton = QPushButton("Add command")
        delButton = QPushButton("x")
        addButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        delButton.setProperty("linkedWidget", weakref.ref(baseWidget))
        delButton.setProperty("linkedGroup", weakref.ref(group))
        delButton.setProperty("linkedLayout", weakref.ref(baseLayout))
        group.setProperty("linkedWidget", weakref.ref(baseWidget))

        listWid.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        addButton.setProperty("linkedList", weakref.ref(listWid))
        addButton.clicked.connect(self.appendCommand)
        delButton.clicked.connect(self.removeGroup)

        buttons.addWidget(addButton)
        buttons.addWidget(delButton)
        layout.addWidget(listWid)
        layout.addLayout(buttons)
        group.setLayout(layout)
        baseLayout.addWidget(group)

        if elem is not None:
            for e in elem["commands"]:
                self.addCommand(listWid, baseWidget, elem=e)

        baseWidget.newGroup.emit(group)

        # self.addCommand(listWid)

    @pyqtSlot()
    def removeGroup(self):
        """
        Delete group on button press
        """
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
        """
        Delete group and emit delGroup signal

        Parameters
        ==========
        group
            QGroupBox object
        layout
            QVBoxLayout widget
        baseWidget
            Main ListBox widget
        """
        layout.removeWidget(group)
        baseWidget.delGroup.emit(group)


handlers = {
    "modules": ModulesLoader,
    "serial": SerialLoader,
    "listmanager": ListViewManager,
}

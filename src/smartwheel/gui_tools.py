import weakref

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap


class IconManager(QObject):
    """
    Instance that manages icons color

    Call `gui_tools.icon_managers["wheel"].colorPixmap(pixmap)` to set icon color during setup, it is going to be stored and updated automatically.

    Updated signal emits when the icons have been updated.

    `gui_tools.icon_managers["sections"]` has separate instance for sections icons
    """

    updated = pyqtSignal()

    def __init__(self):
        super(IconManager, self).__init__()
        self.color = None
        self.color_hex = None
        self.source_pixmaps = []
        self.pixmaps = []
        self.linked_icons = []

    def setIconColor(self, color):
        """
        Set new global icon color, will return False if the color is unchanged.

        Parameters
        ==========
        color
            Color hex
        """
        if color == self.color_hex:
            return False

        self.color_hex = color

        self.color = QColor(color)
        self.updatePixmaps()
        return True

    def colorPixmap(self, pixmap, icon=None):
        """
        Color the pixmap and store it in the instance

        Parameters
        ==========
        pixmap
            QPixmap to update
        icon
            (Optional) Linked QIcon to update
        """
        if self.color == None:
            return

        pixmap = self._applyColor(pixmap)

        if icon:
            new_icon = QIcon(pixmap)
            self.linked_icons.append(weakref.ref(icon))
            icon.swap(new_icon)
        else:
            self.linked_icons.append(None)

        self.pixmaps.append(weakref.ref(pixmap))
        self.source_pixmaps.append(pixmap.copy())

    def _applyColor(self, pixmap):
        """
        Apply color to the pixmap and return it

        Parameters
        ==========
        pixmap
            QPixmap
        """
        qp = QPainter(pixmap)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)

        qp.setBrush(self.color)
        qp.setPen(self.color)
        qp.drawRect(pixmap.rect())
        qp.end()

        return pixmap

    def updatePixmaps(self):
        """
        Iterate over pixmaps and repaint color
        """
        for i in range(len(self.pixmaps)):
            self.pixmaps[i]().swap(self._applyColor(self.source_pixmaps[i]))
            if self.linked_icons[i] is not None and self.linked_icons[i]() is not None:
                self.linked_icons[i]().swap(QIcon(self.pixmaps[i]()))
            # self.colorPixmap(self.pixmaps[i]())

        self.updated.emit()


icon_managers = {
    "wheel": IconManager(),
    "sections": IconManager(),
    "tools": IconManager(),
}

import weakref

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QColor, QPainter, QPixmap


class IconManager(QObject):
    """
    Instance that manages icons color

    Call `gui_tools.icon_managers["wheel"].colorPixmap(pixmap)` to set icon color during setup, it is going to be stored and updated automatically.

    `gui_tools.icon_managers["sections"]` has separate instance for sections icons
    """

    def __init__(self):
        super(IconManager, self).__init__()
        self.color = None
        self.color_hex = None
        self.source_pixmaps = []
        self.pixmaps = []

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

    def colorPixmap(self, pixmap):
        """
        Color the pixmap and store it in the instance

        Parameters
        ==========
        pixmap
            QPixmap to update
        """
        if self.color == None:
            return

        pixmap = self._applyColor(pixmap)

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
            #self.colorPixmap(self.pixmaps[i]())


icon_managers = {"wheel": IconManager(), "sections": IconManager()}

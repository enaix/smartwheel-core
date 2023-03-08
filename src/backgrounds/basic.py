from .base import Background
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class DiagBackground(Background):
    def __init__(self, common_config, conf, canvas):
        super(DiagBackground, self).__init__(common_config, conf, canvas)
        self.setStyle(Qt.BrushStyle.BDiagPattern)
        self.setColor(QColor(self.common_config["wheelTextureColor"]))


class GridBackground(Background):
    def __init__(self, common_config, conf, canvas):
        super(GridBackground, self).__init__(common_config, conf, canvas)
        self.setStyle(Qt.BrushStyle.CrossPattern)
        self.setColor(QColor(self.common_config["wheelTextureColor"]))


brushes = {"diagonal": DiagBackground, "grid": GridBackground}
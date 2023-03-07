from .base import Background
from PyQt6.QtCore import Qt


class DiagBackground(Background):
    def __init__(self, canvas=None):
        super(DiagBackground, self).__init__(canvas)
        self.setStyle(Qt.BrushStyle.BDiagPattern)


class GridBackground(Background):
    def __init__(self, canvas=None):
        super(GridBackground, self).__init__(canvas)
        self.setStyle(Qt.BrushStyle.CrossPattern)


brushes = {"diagonal": DiagBackground, "grid": GridBackground}
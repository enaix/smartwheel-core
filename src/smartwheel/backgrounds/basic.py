from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTransform

from smartwheel import tools
from smartwheel.backgrounds.base import Background


class PatternBackground(Background):
    def __init__(self, common_config, conf, canvas):
        super(PatternBackground, self).__init__(common_config, conf, canvas)
        tools.merge_dicts(
            self.conf, self.common_config(), include_only=["wheelTextureColor"]
        )

        self.conf.updateFunc = self.draw

        self.pattern_map = {
            "Diagonal (right)": Qt.BrushStyle.BDiagPattern,
            "Grid": Qt.BrushStyle.CrossPattern,
            "Diagonal (left)": Qt.BrushStyle.FDiagPattern,
            "Cross": Qt.BrushStyle.DiagCrossPattern,
            "Vertical": Qt.BrushStyle.VerPattern,
            "Horizontal": Qt.BrushStyle.HorPattern,
            "Dots 1": Qt.BrushStyle.Dense7Pattern,
            "Dots 2": Qt.BrushStyle.Dense6Pattern,
            "None": Qt.BrushStyle.NoBrush,
        }

        self.draw()

    def draw(self):
        self.setColor(QColor(self.conf["wheelTextureColor"]))

        tf = QTransform().fromScale(
            self.conf["patternScale"], self.conf["patternScale"]
        )
        self.setTransform(tf)

        if self.pattern_map.get(self.conf["patternType"]) is not None:
            self.setStyle(self.pattern_map[self.conf["patternType"]])
        else:
            return


brushes = {"pattern": PatternBackground}

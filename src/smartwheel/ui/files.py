import importlib
import json
import math
import os
import weakref

from PyQt6.QtCore import *
from PyQt6.QtGui import *

from smartwheel.ui.base import BaseUIElem


class UIElem(BaseUIElem):
    def __init__(self):
        pass

    def loadExtensions(self):
        """
        {
            "types": {
                "img": ["jpg", "jpeg"]
            },
            "conf": {
                "img": {
                    "iconPath": "path_to_icon"
                }
            }
        }
        """
        # TODO flatten extensions to "flatten" array
        # TODO generate dict {"type": "common_name"} to "names"
        # TODO load pixmaps under conf -> <type> -> pixmap
        return None

    def get_files(self):
        files = os.listdir(self.conf["baseFolder"])
        ext = self.loadExtensions()
        self.ent = []
        for f in files:
            entity = {}
            entity["filename"] = f
            f_n = f.split(".")
            e = f_n[len(f_n) - 1].lower()
            entity["extension"] = e
            if e in ext["flatten"]:
                entity["type"] = ext["names"][e]
            else:
                entity["type"] = "none"

            entity["conf"] = ext["conf"][entity["type"]]
        self.files_selector = 0
        # TODO generate files selection list (cur_ext variable)
        self.ent.append(entity)

    def draw_file(self, x, y, f):
        self.parent().qp.drawImage(QPoint(x, y), f["conf"]["pixmap"])
        self.parent().qp.drawText(
            (
                x + self.conf["iconWidth"],
                y,
                self.conf["maxTextWidth"],
                self.conf["iconWidth"],
            ),
            Qt.AlignCenter,
            f["filename"],
        )

    def load_selection_icons(self):
        pass

    def draw_selection(self, circleWidth):
        # TODO draw arrow icons (> <)
        top_left = QPoint(
            self.parent().getX(
                self.conf["selectionAngle"], circleWidth - self.conf["iconWidth"]
            )
        )
        bottom_right = QPoint(
            self.parent().getX(
                self.conf["selectionAngle"],
                circleWidth + self.conf["iconWidth"] * 2 + self.conf["maxTextWidth"],
            )
        )
        # TODO set qbrush
        self.qp.drawRect(top_left, bottom_right)
        self.parent().qp.drawImage(
            (
                top_left,
                QPoint(
                    self.parent().getY(
                        self.conf["selectionAngle"],
                        circleWidth - self.conf["iconWidth"],
                    )
                ),
                self.left_arrow_icon,
            )
        )
        self.parent().qp.drawImage(
            (
                bottom_right,
                QPoint(
                    self.parent().getY(
                        self.conf["selectionAngle"],
                        circleWidth + self.conf["iconWidth"],
                    )
                ),
                self.right_arrow_icon,
            )
        )
        # TODO calculate max text width and draw right arrow
        pass

    def draw_files(self, circleWidth):
        for i in range(len(self.cur_ext)):
            self.draw_file(
                self.parent().getX(self.angle * i, circleWidth),
                self.parent().getY(self.angle * i, circleWidth),
                self.cur_ext[i],
            )

    def draw(self, qp, offset=None):
        if self.conf["isWheelWidthFixed"]:
            circleWidth = self.conf["width"] + self.conf["fixedWheelWidth"]
        else:
            circleWidth = (self.conf["width"] * 6) // 5

        # TODO change window size

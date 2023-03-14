import logging
import math
import os

from PyQt6.QtCore import *
from PyQt6.QtGui import *

from smartwheel import config
from smartwheel.ui.base import BaseUIElem


class UIElem(BaseUIElem):
    def __init__(self, config_file, WConfig):
        super().__init__()
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.loadConfig()
        self.conf.c = {**self.conf, **WConfig}
        self.icon_path = self.conf.get("icon_path", None)
        self.initGUI()
        self.initWidthAnimation()

    def loadConfig(self):
        self.conf = config.Config(self.config_file)
        self.conf.loadConfig()

    def checkOverflow(self, val):
        if val > 359:
            return val - 359
        elif val < 0:
            return 359 - val
        return val

    def processKey(self, event):
        if event["call"] == "keyAction1":
            self.mode = (self.mode + 1) % 3
            self.startWidthAnimation()
        elif event["call"] == "scrollUp" or event["call"] == "scrollDown":
            dlt = self.angle_delta if event["call"] == "scrollUp" else -self.angle_delta
            if self.mode == 0:
                self.hue_selection = self.checkOverflow(self.hue_selection + dlt)
            elif self.mode == 1:
                self.sat_selection = self.checkOverflow(self.sat_selection + dlt)
            elif self.mode == 2:
                self.bri_selection = self.checkOverflow(self.bri_selection + dlt)

            color = QColor.fromHsl(
                int(self.hue_selection),
                int(self.to_map(self.sat_selection)),
                int(self.to_map(self.bri_selection)),
            )
            r, g, b, _ = color.getRgbF()
            self.logger.debug(r, g, b)

            data = self.conf["internal"]["kritaAPI"]["class"].setColor(r, g, b)
            self.conf["internal"]["kritaServer"]["signals"]["send"].emit(data)
            # print(self.hue_selection, self.sat_selection, self.bri_selection)

    def initGUI(self):
        self.hue_selection = self.conf["HueStartAngle"]
        self.sat_selection = self.conf["SatStartAngle"]
        self.bri_selection = self.conf["BriStartAngle"]
        self.mode = 0
        self.angle_delta = self.to_map(1, 0, 359, 0, 255)

        self.delta = 360 // self.conf["selectionWheelEntries"]
        if self.conf["isHSLWidthFixed"]:
            self.hsl_width = self.conf["HSLCircleWidth"]
        else:
            self.hsl_width = self.conf["width"] // 8
        if self.conf["isHSLSelectionWidthFixed"]:
            self.hsl_select_width = self.conf["HSLSelectedCircleWidth"]
        else:
            self.hsl_select_width = self.conf["width"] // 6
        if self.conf["isHSLPaddingFixed"]:
            self.hsl_padding = self.conf["HSLPadding"]
        else:
            self.hsl_padding = self.conf["width"] // 16
        self.hsl_sw = self.hsl_select_width - self.hsl_width

        self.hsl_elem_width = [self.hsl_select_width, self.hsl_width, self.hsl_width]
        self.hsl_padding_width = [self.hsl_padding, self.hsl_padding, self.hsl_padding]

        self.color_window_width = (
            (self.conf["width"] * 3) / 4
            - self.hsl_width * 2
            - self.hsl_select_width
            - self.hsl_padding * 3
            - self.conf["colorWidgetPadding"]
        )

        # ---
        # self.kr_handler = KritaHandler()
        # self.kr_api = KritaAPI()
        # ---

    def _set_width(self, w):
        self.hsl_sw = w

    prop_width = pyqtProperty(int, fset=_set_width)

    def initWidthAnimation(self):
        self.is_anim_running = False
        self.width_anim_start = 0
        self.width_anim_end = self.hsl_select_width - self.hsl_width
        self.width_anim = QPropertyAnimation(self, b"prop_width")
        self.width_anim.setDuration(self.conf["widthAnimDuration"])
        self.width_anim.setStartValue(self.width_anim_start)
        self.width_anim.setEndValue(self.width_anim_end)

    def startWidthAnimation(self):
        self.is_anim_running = True
        # self.width_anim.stop()
        self.width_anim.start()

    def to_map(self, value, i_min=0, i_max=359, o_min=0, o_max=255):
        return o_min + (o_max - o_min) * ((value - i_min) / (i_max - i_min))

    def getX(self, a, w):
        return math.cos(math.radians(a)) * w / 2 + self.conf["cx"]

    def getY(self, a, h):
        return math.sin(math.radians(a)) * h / 2 + self.conf["cy"]

    def drawHueWheel(self, qp, width):
        width -= sum(self.hsl_elem_width[1:3]) + self.hsl_padding * 2
        if self.mode == 0:
            hsl_w = self.hsl_width + self.hsl_sw
        elif self.mode == 1:
            hsl_w = self.hsl_select_width - self.hsl_sw
        else:
            hsl_w = self.hsl_width
        self.hsl_elem_width[0] = hsl_w

        grad = QConicalGradient(
            QPointF(self.conf["cx"], self.conf["cy"]),
            359
            - self.hue_selection
            + self.conf["selectionAngle"]
            - 90
            - (self.delta // 4),
        )
        grad.setColorAt(0, QColor(255, 0, 0))
        grad.setColorAt(1.0 / 6, QColor(255, 255, 0))
        grad.setColorAt(2.0 / 6, QColor(0, 255, 0))
        grad.setColorAt(3.0 / 6, QColor(0, 255, 255))
        grad.setColorAt(4.0 / 6, QColor(0, 0, 255))
        grad.setColorAt(5.0 / 6, QColor(255, 0, 255))
        grad.setColorAt(1, QColor(255, 0, 0))

        qp.setPen(QPen(grad, 1))
        qp.setBrush(QBrush(grad))
        qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), width // 2, width // 2)
        self.drawPadding(qp, width - hsl_w)

        a = self.conf["selectionAngle"] - 90 + (self.delta // 4)
        self.drawColorPoint(
            qp,
            self.getX(a + 90.0, width - hsl_w / 2),
            self.getY(a + 90, width - hsl_w / 2),
            (hsl_w) / 4,
            QColor.fromHsl(int(self.hue_selection), 255, 128),
        )

    def drawSatWheel(self, qp, width):
        width -= self.hsl_elem_width[2] + self.hsl_padding
        if self.mode == 1:
            hsl_w = self.hsl_width + self.hsl_sw
        elif self.mode == 2:
            hsl_w = self.hsl_select_width - self.hsl_sw
        else:
            hsl_w = self.hsl_width
        self.hsl_elem_width[1] = hsl_w

        grad = QConicalGradient(
            QPointF(self.conf["cx"], self.conf["cy"]),
            359
            - self.sat_selection
            + self.conf["selectionAngle"]
            - 90
            - (self.delta // 4),
        )

        grad.setColorAt(0, QColor.fromHsl(int(self.hue_selection), 0, 128))
        grad.setColorAt(1, QColor.fromHsl(int(self.hue_selection), 255, 128))

        qp.setPen(QPen(grad, 1))
        qp.setBrush(QBrush(grad))
        qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), width // 2, width // 2)
        self.drawPadding(qp, width - hsl_w)

        a = self.conf["selectionAngle"] - 90 + (self.delta // 4)
        self.drawColorPoint(
            qp,
            self.getX(a + 90.0, width - hsl_w / 2),
            self.getY(a + 90, width - hsl_w / 2),
            (hsl_w) / 4,
            QColor.fromHsl(
                int(self.hue_selection), int(self.to_map(self.sat_selection)), 128
            ),
        )

    def drawBriWheel(self, qp, width):
        hsl_w = self.hsl_width
        if self.mode == 2:
            hsl_w = self.hsl_width + self.hsl_sw
        elif self.mode == 0:
            hsl_w = self.hsl_select_width - self.hsl_sw
        self.hsl_elem_width[2] = hsl_w

        grad = QConicalGradient(
            QPointF(self.conf["cx"], self.conf["cy"]),
            359
            - self.bri_selection
            + self.conf["selectionAngle"]
            - 90
            - (self.delta // 4),
        )

        grad.setColorAt(0, QColor(0, 0, 0))
        grad.setColorAt(
            0.5,
            QColor.fromHsl(
                int(self.hue_selection), int(self.to_map(self.sat_selection)), 128
            ),
        )
        grad.setColorAt(1, QColor(255, 255, 255))

        qp.setPen(QPen(grad, 1))
        qp.setBrush(QBrush(grad))
        qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), width // 2, width // 2)
        self.drawPadding(qp, width - hsl_w)

        a = self.conf["selectionAngle"] - 90 + (self.delta // 4)

        self.drawColorPoint(
            qp,
            self.getX(a + 90.0, width - hsl_w / 2),
            self.getY(a + 90, width - hsl_w / 2),
            (hsl_w) / 4,
            QColor.fromHsl(
                int(self.hue_selection),
                int(self.to_map(self.sat_selection)),
                int(self.to_map(self.bri_selection)),
            ),
        )

    def drawColorPoint(self, qp, cx, cy, radius, color):
        if qGray(color.rgb()) >= self.conf["colorDotLightnessThreshold"]:
            qp.setPen(
                QPen(
                    QColor(self.conf["colorDotDarkStrokeColor"]),
                    self.conf["colorDotStrokeWidth"],
                )
            )
        else:
            qp.setPen(
                QPen(
                    QColor(self.conf["colorDotLightStrokeColor"]),
                    self.conf["colorDotStrokeWidth"],
                )
            )

        radius -= 0

        qp.setBrush(QBrush(color))
        qp.drawEllipse(QPointF(cx, cy), radius, radius)

    def drawPadding(self, qp, width):
        qp.setPen(QPen())
        qp.setBrush(QBrush(QColor(self.conf["bgWheelColor"])))
        qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), width // 2, width // 2)

    def drawColorWindow(self, qp, color, width, offset):
        qp.setPen(
            QPen(
                QColor(self.conf["colorDotLightStrokeColor"]),
                self.conf["colorDotStrokeWidth"],
            )
        )

        width = min(width, self.conf["colorWidgetMaxWidth"] / 2)

        qp.setBrush(QBrush(color))
        if self.conf["colorWidgetShape"] == "circle":
            qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), width, width)
        elif self.conf["colorWidgetShape"] == "square":
            qp.drawRect(
                QRect(
                    self.conf["cx"] - width,
                    self.conf["cy"] - width,
                    width * 2,
                    width * 2,
                )
            )
        elif self.conf["colorWidgetShape"] == "hybrid":
            qp.drawRoundedRect(
                QRectF(
                    self.conf["cx"] - width,
                    self.conf["cy"] - width,
                    width * 2,
                    width * 2,
                ),
                self.conf["wheelWidth"] - offset,
                self.conf["wheelWidth"] - offset,
                Qt.SizeMode.RelativeSize,
            )

    def draw(self, qp, offset=None):
        if self.width_anim.state() == QAbstractAnimation.State.Stopped:
            self.is_anim_running = False
        self.drawBriWheel(qp, (self.conf["width"] * 3) // 4 + offset)
        self.drawSatWheel(qp, (self.conf["width"] * 3) // 4 + offset)
        self.drawHueWheel(qp, (self.conf["width"] * 3) // 4 + offset)

        self.drawColorWindow(
            qp,
            QColor.fromHsl(
                int(self.hue_selection),
                int(self.to_map(self.sat_selection)),
                int(self.to_map(self.bri_selection)),
            ),
            (self.color_window_width + offset) / 2,
            offset,
        )

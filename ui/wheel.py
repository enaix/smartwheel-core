import json
import math
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.base import BaseUIElem
import importlib
import os
import weakref

class Section():
    def __init__(self, start_angle, end_angle, parent, module=None):
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.angle = (start_angle + end_angle) // 2
        self.delta = 0
        self.init_angle = parent._angle
        self.is_selected = False
        self.module = module
        self.parent = weakref.ref(parent)
        self.pixmap = None
        if self.module is not None:
            self.load_module()
        if self.pixmap is not None:
            self.scale_pixmap()

    def load_module(self):
        #mod = importlib.import_module(self.module["name"])
        #ui = mod.UIElem(self.module["config"], self.parent.conf)
        #self.module["class"] = ui
        if self.module["class"].icon_path is None:
            self.pixmap = None #QImage(os.path.join(self.parent().conf["iconsFolder"], "folder.png"))
        else:
            self.pixmap = QImage(os.path.join(self.parent().conf["iconsFolder"], self.module["class"].icon_path))

    def draw_module(self, qp):
        if self.module is not None:
            self.module["class"].draw(qp, self.parent()._sections_pos)

    def update_vars(self):
        self.delta = self.parent()._angle - self.init_angle

    def scale_pixmap(self):
        w = self.parent().conf["pixmapScale"]
        self.pixmap.width = w
        self.pixmap.height = w
        self.pixmap = self.pixmap.scaled(QSize(w, w), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def reload_module(self, module):
        self.module = module
        self.pixmap = None
        if self.module is not None:
            self.load_module()
        if self.pixmap is not None:
            self.scale_pixmap()

    def draw_icon(self, cx, cy):
        if self.pixmap is not None:
            self.parent().qp.drawImage(QPointF(cx, cy), self.pixmap)

    def calculate_coords(self, a, start, end):
        x1 = self.parent().getX(a, start)
        x2 = self.parent().getX(a, end)
        y1 = self.parent().getY(a, start)
        y2 = self.parent().getY(a, end)
        return x1, x2, y1, y2

    def draw(self, qp, start_w, end_w):
        end_w -= self.parent()._sections_pos
        self.update_vars()
        x1, x2, y1, y2 = self.calculate_coords(self.end_angle + self.delta, start_w, end_w)

        xa1, xa2, ya1, ya2 = self.calculate_coords(self.start_angle + self.delta, start_w + self.parent().conf["pixmapScale"], end_w)

        xb1, xb2, yb1, yb2 = self.calculate_coords(self.end_angle + self.delta, start_w + self.parent().conf["pixmapScale"], end_w)

        brush = QBrush()
        pen = QPen(QColor(self.parent().conf["selectionWheelFG"]), 1, Qt.SolidLine)
        qp.setBrush(brush)
        qp.setPen(pen)
        qp.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        self.draw_icon(((xa1+xa2)//2 + (xb1+xb2)//2)//2 - self.parent().conf["pixmapScale"]//2, ((ya1+ya2)//2 + (yb1+yb2)//2)//2 - self.parent().conf["pixmapScale"]//2)

class UIElem(BaseUIElem):
    def __init__(self, config_file, WConfig, modules, force_update):
        super().__init__()
        self.config_file = config_file
        self.modules = modules
        self.force_update = force_update
        self.is_anim_running = False
        self.cur_section = 0
        self.loadConfig()
        self.conf = {**self.conf, **WConfig}
        self.initSections()
        self.initAnimation()
        self.initShadowAnimation()
        self.initSectionsAnimation()
        self._opacity = 0
        self._sections_pos = 0
        self.global_shadow = False

    def _set_angle(self, a):
        self._angle = a

    def _set_opacity(self, o):
        self._opacity = o

    def _set_sections_pos(self, pos):
        self._sections_pos = pos

    prop_angle = pyqtProperty(int, fset=_set_angle)
    prop_opacity = pyqtProperty(int, fset=_set_opacity)
    prop_sections = pyqtProperty(int, fset=_set_sections_pos)

    def loadConfig(self):
        with open(self.config_file, "r") as f:
            self.conf = json.load(f)

    def getX(self, a, w):
        return math.cos(math.radians(a)) * w // 2 + self.conf["cx"]

    def getY(self, a, h):
        return math.sin(math.radians(a)) * h // 2 + self.conf["cy"]

    def drawSelection(self, circleWidth, circleHeight):
        # Draw selection wheel
        width = self.conf["width"]
        height = self.conf["height"]
        
        pen = QPen(QColor(self.conf["selectionWheelFG"]), 1, Qt.SolidLine)
        brush = QBrush(QColor(self.conf["selectionWheelBG"]))
        self.qp.setBrush(brush)
        self.qp.setPen(pen)
        self.qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), width // 2, height // 2)

        self.drawSections(width, circleWidth)

    def scrollModule(self, up):
        old_selection = self.cur_section
        if up:
            self.cur_section = (self.cur_section - 1) % len(self.sections)
        else:
            self.cur_section = (self.cur_section + 1) % len(self.sections)
        self.sections[self.cur_section].is_selected = True
        self.sections[old_selection].is_selected = False
    
    def processKey(self, up):
        self.scrollModule(up)

        if self.is_scroll_anim_running:
            self.updateAnimation(up)
        else:
            self.startAnimation(up)
        self.startShadowAnimation()
        if self.sections_timer.isActive():
            self.sections_timer.start(self.conf["sectionsHideTimeout"])
        else:
            self.sections_timer.start(self.conf["sectionsHideTimeout"] + self.conf["sectionsAnimationDuration"])
        self.showSections()
        #self.sections_timer.singleShot(self.conf["sectionsHideTimeout"] + self.conf["sectionsAnimationDuration"], self.hideSections)
        #self.startSectionsAnimation(True)

    def openWheel(self):
        self.sections_timer.stop()
        self.showSections()
    
    def selectModule(self):
        self.sections_timer.stop()
        self.hideSections()

    def quickSwitch(self, up):
        self.scrollModule(up)

        if self.is_scroll_anim_running:
            self.updateAnimation(up)
        else:
            self.startAnimation(up)
        self.startShadowAnimation()

        self.sections_timer.stop()

    def getModule(self, i):
        if i >= len(self.modules):
            return None
        return self.modules[i]

    def initSections(self):
        self.delta = 360 // self.conf["selectionWheelEntries"]
        self._angle = self.conf["selectionAngle"]
        self.sections = [Section(self.delta*i + self.conf["selectionAngle"] - self.delta//4, self.delta*i + self.delta + self.conf["selectionAngle"] - self.delta//4, self, self.getModule(i)) for i in range(self.conf["selectionWheelEntries"])]
        self.sections[0].is_selected = True
        self.cur_section = 0

    def resetUI(self):
        for i in range(len(self.sections)):
            self.sections[i].is_selected = False
        self.sections[i].is_selected = True
        self.cur_section = 0

        self.sections_timer.stop()

        self.is_scroll_anim_running = False
        self.anim.stop()
        #self.is_shadow_anim_running = False
        #self.shadow_anim.stop()
        self.is_sections_anim_running = False
        self.sections_anim.stop()

        self._angle = self.conf["selectionAngle"]
        self.anim_angle = self._angle
        self._sections_pos = 0
        self._opacity = 0
        
        self.global_shadow = True
        self.startShadowAnimation()

    def reloadModules(self, modules):
        self.resetUI()
        self.modules = modules
        for i in range(len(self.sections)):
            self.sections[i].reload_module(self.getModule(i))

    def getSectionsModules(self):
        return [x.module for x in self.sections]

    def getCurModule(self):
        return self.cur_section

    def initAnimation(self):
        self.is_scroll_anim_running = False
        self.anim_angle = self.conf["selectionAngle"]
        self.anim_start = self.anim_angle
        self.anim_end = self.anim_angle + self.delta
        self.anim = QPropertyAnimation(self, b"prop_angle")
        self.anim.setDuration(self.conf["scrollAnimationDuration"])

    def startAnimation(self, up, a=None):
        self.is_scroll_anim_running = True
        if a is not None:
            self.anim_start = a
        else:
            self.anim_start = self.anim_angle
        if up:
            self.anim_angle += self.delta
            self.anim_end = self.anim_angle
        else:
            self.anim_angle -= self.delta
            self.anim_end = self.anim_angle
        self.anim.setStartValue(self.anim_start)
        self.anim.setEndValue(self.anim_end)
        self.anim.start()

    def updateAnimation(self, up):
        self.anim.stop()
        self.startAnimation(up, a=self._angle)

    def drawShadow(self, cw):
        if self._opacity == 0:
            return
        pen = QPen(QColor(self.conf["wheelTextureColor"]))
        self.qp.setPen(pen)
        brush = QBrush(QColor("#" + str(hex(self._opacity).split('x')[-1].zfill(2)) + self.conf["bgWheelColor"][1:]))
        self.qp.setBrush(brush)
        self.qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), cw // 2, cw // 2)

    def initShadowAnimation(self):
        self.is_shadow_anim_running = False
        self.shadow_anim_start = 255
        self.shadow_anim_end = 0
        self.shadow_anim = QPropertyAnimation(self, b"prop_opacity")
        self.shadow_anim.setDuration(self.conf["shadowAnimationDuration"])

    def startShadowAnimation(self):
        dur = self.conf["shadowAnimationDuration"]
        mid_key = 0.5
        if self.is_shadow_anim_running == True:
            self.shadow_anim.stop()
            mid_key = 0.7
            dur *= 1.5
        self.shadow_anim.setKeyValueAt(0, self.shadow_anim_start)
        self.shadow_anim.setKeyValueAt(mid_key, self.shadow_anim_start)
        self.shadow_anim.setKeyValueAt(1, self.shadow_anim_end)
        #self.shadow_anim.setEndValue(self.shadow_anim_end)
        self.shadow_anim.setDuration(int(dur))
        self.shadow_anim.start()
        self.is_shadow_anim_running = True

    def initSectionsAnimation(self):
        self.is_sections_anim_running = False
        self.is_sections_hidden = False
        self.sections_anim_start = 0
        self.sections_timer = QTimer()
        self.sections_timer.setSingleShot(True)
        #self.sections_timer.setInterval(self.conf["sectionsHideTimeout"])
        #self.sections_timer.singleShot(self.conf["sectionsHideTimeout"], self.hideSections)
        self.sections_timer.timeout.connect(self.hideSections)
        self.sections_timer.start(self.conf["sectionsHideTimeout"])
        if self.conf["isWheelWidthFixed"]:
            self.sections_anim_end = self.conf["fixedWheelWidth"]
        else:
            self.sections_anim_end = (self.conf["width"] * 1) // 4
        self.sections_anim = QPropertyAnimation(self, b"prop_sections")
        self.sections_anim.setDuration(self.conf["sectionsAnimationDuration"])

    def startSectionsAnimation(self, hide):
        self.is_sections_anim_running = True
        if hide:
            self.sections_anim.setStartValue(self._sections_pos)
            self.sections_anim.setEndValue(self.sections_anim_end)
            self.is_sections_hidden = True
        else:
            self.sections_anim.setStartValue(self._sections_pos)
            self.sections_anim.setEndValue(self.sections_anim_start)
            self.is_sections_hidden = False
        self.sections_anim.start()
        self.force_update()

    def hideSections(self):
        if not self.is_sections_hidden:
            self.startSectionsAnimation(True)

    def showSections(self):
        if self.is_sections_hidden:
            self.startSectionsAnimation(False)

    def drawSections(self, w, cw):
        for s in self.sections:
            s.draw(self.qp, w, cw)
        pen = QPen(QColor(self.conf["pointerColor"]), 3, Qt.SolidLine)
        self.qp.setPen(pen)
        # draw pointer
        self.qp.drawArc(self.conf["corner_x"]-self.conf["pointerMargin"], self.conf["corner_y"]-self.conf["pointerMargin"], self.conf["width"]+self.conf["pointerMargin"], self.conf["height"]+self.conf["pointerMargin"], - 90*16 + self.conf["selectionAngle"]*16 + (self.delta//4)*16, - self.delta*16)
        #p = QPalette()
        #gradient = QConicalGradient(self.conf["cx"], self.conf["cy"], self.conf["selectionAngle"])
        #gradient.setColorAt(0.0, QColor.fromHsv(0, 0, 255))
        #gradient.setColorAt(1.0, QColor.fromHsv(255, 0, 255))
        #self.qp.setBrush(QBrush(gradient))
        #self.qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), cw // 3, cw // 3)

    def drawMainWheel(self, circleWidth, circleHeight):
        # Draw main wheel
        color = self.conf["bgWheelColor"]
        if self.conf["drawWheelCircle"]:
            color = self.conf["wheelTextureColor"]
        pen = QPen(QColor(color), 1, Qt.SolidLine)
        self.qp.setPen(pen)
        brush = QBrush(QColor(self.conf["bgWheelColor"]))
        self.qp.setBrush(brush)
        self.qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), circleWidth // 2, circleHeight // 2)
        brush = QBrush(QColor(self.conf["wheelTextureColor"]), Qt.BDiagPattern)
        self.qp.setBrush(brush)
        self.qp.drawEllipse(QPoint(self.conf["cx"], self.conf["cy"]), circleWidth // 2, circleHeight // 2)

    def draw(self, qp):
        if self.anim.state() == 0:
            self.is_scroll_anim_running = False
        if self.shadow_anim.state() == 0:
            self.global_shadow = False
            self.is_shadow_anim_running = False
        if self.sections_anim.state() == 0:
            self.is_sections_anim_running = False
        self.is_anim_running = self.is_scroll_anim_running or self.is_shadow_anim_running or self.is_sections_anim_running
        if self.conf["isWheelWidthFixed"]:
            circleWidth = self.conf["width"] - self.conf["fixedWheelWidth"] + self._sections_pos
            circleHeight = self.conf["height"] - self.conf["fixedWheelWidth"] + self._sections_pos
        else:
            circleWidth = (self.conf["width"] * 3) // 4 + self._sections_pos
            circleHeight = (self.conf["height"] * 3) // 4 + self._sections_pos
        
        self.qp = qp

        self.drawSelection(circleWidth, circleHeight)

        self.drawMainWheel(circleWidth, circleHeight)

        self.sections[self.cur_section].draw_module(self.qp)
       
        if self.global_shadow:
            self.drawShadow(self.conf["width"])
        else:
            self.drawShadow(circleWidth)


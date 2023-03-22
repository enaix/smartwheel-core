import os
import subprocess
import time

from PyQt6.QtCore import *
from PyQt6.QtGui import *

from smartwheel import config, gui_tools
from smartwheel.tools import merge_dicts
from smartwheel.ui.base import BaseUIElem


class ThreadWrapper(QObject):
    update = pyqtSignal(list)


class UIThread(QRunnable):
    def __init__(self, sleep_ms):
        super(UIThread, self).__init__()
        self.wrapper = ThreadWrapper()
        self.unix_meta_old = ""
        self.unix_track_meta_old = []
        self.last_text = []
        self.sleep_ms = sleep_ms
        self.shutdown = False

    @pyqtSlot()
    def run(self):
        while not self.shutdown:
            if os.name == "posix":
                try:
                    res = self.fetchMediaUnix()
                except BaseException as e:
                    print(e)
                    return

            elif os.name == "nt":
                try:
                    res = self.fetchMediaWin()
                except BaseException as e:
                    print(e)
                    return
            else:
                res = ["--", "--", "--", "--"]

            if not res == self.last_text:
                self.wrapper.update.emit(res)
                self.last_text = res

            time.sleep(self.sleep_ms)

    def fetchMediaWin(self):
        return ["--", "--", "--", "--"]

    def findProp(self, s, prop):
        if prop.find(":") != -1:
            exp = lambda x: x[1]
        else:
            exp = lambda x: x[1].split(":")[1]
        for i in s:
            if exp(i) == prop:
                return " ".join(i[2:])
        return "--"

    def fetchMediaUnix(self):
        # TODO move to gi.repository.Playerctl
        raw = subprocess.run(["playerctl", "metadata"], capture_output=True).stdout
        pos = subprocess.run(["playerctl", "position"], capture_output=True).stdout

        if raw == "No players found":
            return ["--", "--", "--", "--"]

        if str(raw) + str(pos) == self.unix_meta_old:
            return self.unix_track_meta_old

        meta = list(
            map(
                lambda x: list([i.decode("utf-8") for i in x.split() if i]),
                raw.splitlines(),
            )
        )

        track = self.findProp(meta, "title")

        if track == "--":
            track = self.findProp(meta, "url").split("/")[-1]

        artist = self.findProp(meta, "artist")
        length = self.findProp(meta, "mpris:length")
        start = "--"
        end = "--"

        if not length == "--":
            length = int(int(length) / 1000000)
            pos = int(float(pos.decode("utf-8")))
            start = time.strftime("%M:%S", time.gmtime(pos))
            end = time.strftime("%M:%S", time.gmtime(length))

        self.unix_meta_old = str(raw) + str(pos)
        self.unix_track_meta_old = [track, artist, start, end]

        return [track, artist, start, end]


class UIElem(BaseUIElem):
    updateSignal = pyqtSignal()

    def __init__(self, config_file, WConfig):
        super().__init__()
        self.config_file = config_file
        self.loadConfig()
        merge_dicts(self.conf, WConfig)
        self.icon_path = self.conf["icon_path"]
        self.thread = UIThread(self.conf["mediaFetchSleep"])
        self.thread.wrapper.update.connect(self.updateText)
        self.text = ["--", "--", "--", "--"]

        self.initGUI()

    def loadConfig(self):
        self.conf = config.Config(self.config_file)
        self.conf.loadConfig()

    def initGUI(self):
        self.updateVars()
        self.pixmap = QPixmap(
            os.path.join(self.conf["iconsFolder"], self.conf["icons"][0])
        )
        self.pixmap = self.pixmap.scaled(
            QSize(self.pix_width, self.pix_height),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        gui_tools.icon_managers["wheel"].colorPixmap(self.pixmap)

    def updateVars(self, offset=0):
        self.width = ((self.conf["width"] + offset) * 3) // 4
        self.height = ((self.conf["height"] + offset) * 3) // 4
        self.pix_width = (self.conf["width"] * 3) // 16
        self.pix_height = (self.conf["height"] * 3) // 16
        self.text_width = ((self.conf["width"] + offset) * 3) // 4
        self.text_height = (self.conf["height"] + offset) // 8

    @pyqtSlot(list)
    def updateText(self, text):
        self.text = text
        self.updateSignal.emit()

    def drawText(self, qp, color, t_font, size, pos, text):
        pen = QPen(QColor(color))
        font = QFont(t_font, size)
        qp.setPen(pen)
        qp.setFont(font)
        qp.drawText(
            QRect(
                self.conf["cx"] - self.text_width // 2,
                self.conf["cy"] - self.text_height // 2,
                self.text_width,
                self.text_height * pos,
            ),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

    def drawHeaderText(self, qp, t):
        self.drawText(
            qp,
            self.conf["majorTextColor"],
            self.conf["textHeaderFont"],
            self.conf["textHeaderSize"],
            1,
            t,
        )

    def drawBottomText(self, qp, t):
        self.drawText(
            qp,
            self.conf["majorTextColor"],
            self.conf["bottomTextFont"],
            self.conf["bottomTextSize"],
            2,
            t,
        )

    def drawTrackSeek(self, qp, t1, t2):
        self.drawText(
            qp,
            self.conf["majorTextColor"],
            self.conf["seekTextFont"],
            self.conf["seekTextSize"],
            3,
            t1 + " / " + t2,
        )

    def draw(self, qp, offset):
        self.updateVars(offset)
        qp.drawPixmap(
            QPointF(
                self.conf["cx"] - self.pix_width // 2,
                self.conf["cy"] - self.pix_height * 1.5,
            ),
            self.pixmap,
        )

        track, artist, start, end = self.text

        self.drawHeaderText(qp, track)
        self.drawBottomText(qp, artist)
        self.drawTrackSeek(qp, start, end)

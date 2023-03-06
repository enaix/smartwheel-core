import config
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.base import BaseUIElem
import os
import subprocess
import time
from tools import merge_dicts


class UIElem(BaseUIElem):
    def __init__(self, config_file, WConfig):
        super().__init__()
        self.config_file = config_file
        self.loadConfig()
        merge_dicts(self.conf, WConfig)
        self.icon_path = self.conf["icon_path"]
        self.meta_old = ""
        self.track_meta_old = []
        self.initGUI()

    def loadConfig(self):
        self.conf = config.Config(self.config_file)
        self.conf.loadConfig()

    def initGUI(self):
        self.updateVars()
        self.pixmap = QImage(os.path.join(self.conf["iconsFolder"], self.conf["icons"][0]))
        self.pixmap = self.pixmap.scaled(QSize(self.pix_width, self.pix_height), Qt.KeepAspectRatio,
                                         Qt.SmoothTransformation)

    def updateVars(self, offset=0):
        self.width = ((self.conf["width"] + offset) * 3) // 4
        self.height = ((self.conf["height"] + offset) * 3) // 4
        self.pix_width = (self.conf["width"] * 3) // 16
        self.pix_height = (self.conf["height"] * 3) // 16
        self.text_width = ((self.conf["width"] + offset) * 3) // 4
        self.text_height = (self.conf["height"] + offset) // 8

    def findProp(self, s, prop):
        if prop.find(':') != -1:
            exp = lambda x: x[1]
        else:
            exp = lambda x: x[1].split(':')[1]
        for i in s:
            if exp(i) == prop:
                return ' '.join(i[2:])
        return "--"

    def fetchMedia(self):
        if not os.name == "posix":
            print("Warning: non-POSIX OS detected. Here be dragons!")
        raw = subprocess.run(["playerctl", "metadata"], capture_output=True).stdout
        pos = subprocess.run(["playerctl", "position"], capture_output=True).stdout
        if raw == "No players found":
            return "--", "--", "--", "--"
        if str(raw) + str(pos) == self.meta_old:
            return self.track_meta_old
        meta = list(map(lambda x: list([i.decode('utf-8') for i in x.split() if i]), raw.splitlines()))
        track = self.findProp(meta, 'title')
        if track == "--":
            track = self.findProp(meta, 'url').split('/')[-1]
        artist = self.findProp(meta, 'artist')
        length = self.findProp(meta, 'mpris:length')
        start = "--"
        end = "--"
        if not length == "--":
            length = int(int(length) / 1000000)
            pos = int(float(pos.decode('utf-8')))
            start = time.strftime("%M:%S", time.gmtime(pos))
            end = time.strftime("%M:%S", time.gmtime(length))
        self.meta_old = str(raw) + str(pos)
        self.track_meta_old = [track, artist, start, end]
        return track, artist, start, end

    def drawText(self, qp, color, t_font, size, pos, text):
        pen = QPen(QColor(color))
        font = QFont(t_font, size)
        qp.setPen(pen)
        qp.setFont(font)
        qp.drawText(
            QRect(self.conf["cx"] - self.text_width // 2, self.conf["cy"] - self.text_height // 2, self.text_width,
                  self.text_height * pos), Qt.AlignCenter, text)

    def drawHeaderText(self, qp, t):
        self.drawText(qp, self.conf["style"]["textHeaderColor"], self.conf["style"]["textHeaderFont"],
                      self.conf["style"]["textHeaderSize"], 1, t)

    def drawBottomText(self, qp, t):
        self.drawText(qp, self.conf["style"]["bottomTextColor"], self.conf["style"]["bottomTextFont"],
                      self.conf["style"]["bottomTextSize"], 2, t)

    def drawTrackSeek(self, qp, t1, t2):
        self.drawText(qp, self.conf["style"]["seekTextColor"], self.conf["style"]["seekTextFont"],
                      self.conf["style"]["seekTextSize"], 3, t1 + " / " + t2)

    def draw(self, qp, offset):
        self.updateVars(offset)
        qp.drawImage(QPointF(self.conf["cx"] - self.pix_width // 2, self.conf["cy"] - self.pix_height * 1.5),
                     self.pixmap)
        try:
            track, artist, start, end = self.fetchMedia()
        except BaseException:
            track, artist, start, end = ("--", "--", "--", "--")
        self.drawHeaderText(qp, track)
        self.drawBottomText(qp, artist)
        self.drawTrackSeek(qp, start, end)

    # TODO add another update loop

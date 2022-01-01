from krita import *
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QThread, pyqtSignal
import socket
import os
import json
import time

class WheelSocket(QThread):
    def __init__(self, signal):
        super().__init__()
        self.timeout = 1
        self.signal = signal

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def run(self):
        self.openSocket()
        self.readSocket()

    def openSocket(self):
        self.client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        while self.isRunning():
            if os.path.exists("/tmp/krita_socket"):
                try:
                    self.client.connect("/tmp/krita_socket")
                    break
                except BaseException:
                    time.sleep(self.timeout)
                #print("Connection established.")
            else:
                #print("Could not connect to the socket")
                time.sleep(self.timeout)
                #os.exit(1)

    def reconnect(self):
        try:
            self.client.close()
        except BaseException:
            return
        self.openSocket()

    def readSocket(self):
        while self.isRunning():
            try:
                raw = self.client.recv(1024)
            except BaseException:
                time.sleep(self.timeout)
                #self.reconnect()
                continue
            if not raw:
                #print("Shutting down...")
                #break
                time.sleep(self.timeout)
                continue
            data = raw.decode('utf-8')

            try:
                js = json.loads(data)
            except BaseException:
                continue
            act = js.get("action", None)
            if act is not None:
                #processAction(app, js)
                self.signal.emit(js)

class WheelExtension(Extension):
    action = pyqtSignal(dict)
    
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.action.connect(self.processAction)

    def setup(self):
        self.ws = WheelSocket(self.action)
        self.ws.start()

    def createActions(self, window):
        action = window.createAction("smartwheel", "SmartWheel", "tools/scripts")

    def toManagedColor(self, color):
        #r, g, b = [0.9862973983367667, 0.18240634775310902, 0.0019378957808804456]
        #r, g, b = *color
        #_, r, g, b = rgb.qRgb()
        
        mc = ManagedColor("RGBA", "F32", "")
        comp = mc.components()
        comp[0] = color[2]
        comp[1] = color[1]
        comp[2] = color[0]
        mc.setComponents(comp)
        return mc

    def setKritaColor(self, color):
        cur_view = self.app.activeWindow().activeView()
        if cur_view != 0:
            cur_view.setForeGroundColor(color)

    def processAction(self, data):
        if data["action"] == "set_color":
            color = data["properties"]["rgb"] # [r, g, b]
            #qc = QColor(*color)
            mc = self.toManagedColor(color)
            self.setKritaColor(mc)

app = Krita.instance()
ext = WheelExtension(app)
app.addExtension(ext)

#ext.setup()
#time.sleep(10)



from .base import Background
from PyQt6.QtCore import Qt, QByteArray, QDataStream
from PyQt6.QtGui import QPixmap, QImage
import matplotlib.pyplot as plt
import numpy as np
import io
import os
import common


class ContourBackground(Background):
    def __init__(self, common_config, conf, canvas):
        super(ContourBackground, self).__init__(common_config, conf, canvas)
        self.setTexture(self.loadPixmap())
        #self.setStyle(Qt.BrushStyle.BDiagPattern)

    def genContour(self):
        plt.rcParams['figure.facecolor'] = self.conf["backgroundColor"]
        plt.figure(figsize=(1, 1), dpi=self.common_config["width"] + 10)
        plt.axes([0, 0, 1, 1])

        def function(x,y):
            return np.sin(x) + np.cos(10 + y * x)

        # Generating data
        x= np.linspace(0,5,50)
        y= np.linspace(0,5,40)
        x,y = np.meshgrid(x,y)
        z = function(x,y)

        # Plotting the contour plot
        plt.contour(x,y,z,colors=self.common_config["wheelTextureColor"])

        # Adding details to the plot
        plt.title('sin(x) + cos(10+y*x)')
        plt.xlabel('x-axis')
        plt.ylabel('y-axis')
        plt.axis('off')
        plt.box('off')

        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)

        if self.conf["useCache"]:
            filepath = common.cache_manager.save("background_contour", "contour1.png", self.conf)
            with open(filepath, 'wb') as f:
                f.write(img_buf.getvalue())
        
        img_buf.seek(0)
        
        return self.contourToPixmap(img_buf)
    
    def checkCache(self, conf):
        params = ["backgroundColor"]

        for p in params:
            if not self.conf.get(p) == conf.get(p):
                return False
        return True

    def loadPixmap(self):
        if self.conf["useCache"]:
            ok, filepath, conf = common.cache_manager.load("background_contour", "contour1.png")
            if ok and self.checkCache(conf):
                pix = QPixmap()
                pix.load(filepath)
                return pix
            
        pix = self.genContour()
        
        return pix
                

    def contourToPixmap(self, img_buf):
        bytes = img_buf.read()
        pix = QPixmap()
        pix.loadFromData(bytes, format="png")
        return pix



brushes = {"contour": ContourBackground}
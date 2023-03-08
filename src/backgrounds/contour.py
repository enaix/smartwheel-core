from .base import Background
from PyQt6.QtCore import Qt, QByteArray, QDataStream
from PyQt6.QtGui import QPixmap, QImage
import matplotlib.pyplot as plt
import numpy as np
import io
import os
import common
import random
import string


class ContourBackground(Background):
    def __init__(self, common_config, conf, canvas):
        super(ContourBackground, self).__init__(common_config, conf, canvas)
        self.conf["wheelTextureColor"] = self.common_config["wheelTextureColor"]
        self.setTexture(self.loadPixmap())
        #self.setStyle(Qt.BrushStyle.BDiagPattern)

    def genContour(self):
        if self.conf["randomSeed"]:
            seed = ''.join(random.sample(string.ascii_lowercase+string.digits, 10))
            self.conf["seed"] = seed
            print(seed)
        
        random.seed(self.conf["seed"])
        
        plt.rcParams['figure.facecolor'] = self.conf["backgroundColor"]
        plt.figure(figsize=(1, 1), dpi=self.common_config["width"] + 10)
        plt.axes([0, 0, 1, 1])

        sign = lambda: (-1)**int(random.randint(1, 2))
        
        def getXY(x, y):
            a = random.randint(0, 2)
            
            if a == 0:
                return sign()*x + sign()*y + random.randint(-20, 20)
            if a == 1:
                return sign()*x + random.randint(-20, 20)
            if a == 2:
                return sign()*y + random.randint(-20, 20)

        def function(x,y):
            return sign()*np.sin(getXY(x, y)) + sign()*np.cos(getXY(x, y))

        # Generating data
        x= np.linspace(0,5,50)
        y= np.linspace(0,5,50)
        x,y = np.meshgrid(x,y)
        z = function(x,y)

        # Plotting the contour plot
        plt.contour(x,y,z,colors=self.conf["wheelTextureColor"])

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
        params = ["backgroundColor", "wheelTextureColor", "seed"]

        for p in params:
            if not self.conf.get(p) == conf.get(p):
                return False
        return True

    def loadPixmap(self):
        if self.conf["useCache"] and not self.conf["randomSeed"]:
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
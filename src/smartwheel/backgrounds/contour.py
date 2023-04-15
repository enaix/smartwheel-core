import io
import os
import random
import string

import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtGui import QPixmap

from smartwheel import common, tools
from smartwheel.backgrounds.base import Background


class ContourBackground(Background):
    def __init__(self, common_config, conf, canvas):
        super(ContourBackground, self).__init__(common_config, conf, canvas)
        tools.merge_dicts(
            self.conf, self.common_config(), include_only=["wheelTextureColor"]
        )
        self.setTexture(self.loadPixmap())

        self.conf.updateFunc = self.updatePixmap
        # self.conf.updated.connect(self.updatePixmap)

    def genContour(self):
        if self.conf["randomSeed"]:
            seed = random.randint(0, 100000)
            self.conf["seed"] = seed

        random.seed(self.conf["seed"])

        plt.rcParams["figure.facecolor"] = self.conf["backgroundColor"]
        plt.figure(figsize=(1, 1), dpi=self.common_config()["width"] + 10)
        plt.axes([0, 0, 1, 1])

        def perlin(x, y, seed=0):
            # permutation table
            np.random.seed(seed)
            p = np.arange(256, dtype=int)
            np.random.shuffle(p)
            p = np.stack([p, p]).flatten()
            # coordinates of the top-left
            xi, yi = x.astype(int), y.astype(int)
            # internal coordinates
            xf, yf = x - xi, y - yi
            # fade factors
            u, v = fade(xf), fade(yf)
            # noise components
            n00 = gradient(p[p[xi] + yi], xf, yf)
            n01 = gradient(p[p[xi] + yi + 1], xf, yf - 1)
            n11 = gradient(p[p[xi + 1] + yi + 1], xf - 1, yf - 1)
            n10 = gradient(p[p[xi + 1] + yi], xf - 1, yf)
            # combine noises
            x1 = lerp(n00, n10, u)
            x2 = lerp(n01, n11, u)  # FIX1: I was using n10 instead of n01
            return lerp(x1, x2, v)  # FIX2: I also had to reverse x1 and x2 here

        def lerp(a, b, x):
            "linear interpolation"
            return a + x * (b - a)

        def fade(t):
            "6t^5 - 15t^4 + 10t^3"
            return 6 * t**5 - 15 * t**4 + 10 * t**3

        def gradient(h, x, y):
            "grad converts h to the right gradient vector and return the dot product with (x,y)"
            vectors = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])
            g = vectors[h % 4]
            return g[:, :, 0] * x + g[:, :, 1] * y

        sign = lambda: (-1) ** int(random.randint(1, 2))

        def getXY(x, y):
            a = random.randint(0, 2)

            if a == 0:
                return sign() * x + sign() * y + random.randint(-20, 20)
            if a == 1:
                return sign() * x + random.randint(-20, 20)
            if a == 2:
                return sign() * y + random.randint(-20, 20)

        def sine_family(x, y):
            return sign() * np.sin(getXY(x, y)) + sign() * np.cos(getXY(x, y))

        def perlin_gen(x, y):
            return perlin(x, y, seed=self.conf["seed"])

        # Generating data
        x = np.linspace(0, 5, 50)
        y = np.linspace(0, 5, 50)
        x, y = np.meshgrid(x, y)

        if self.conf["generator"] == "Perlin":
            z = perlin_gen(x, y)
        else:
            z = sine_family(x, y)

        # Plotting the contour plot
        plt.contour(x, y, z, colors=self.conf["wheelTextureColor"])

        # Adding details to the plot
        plt.title("sin(x) + cos(10+y*x)")
        plt.xlabel("x-axis")
        plt.ylabel("y-axis")
        plt.axis("off")
        plt.box("off")

        img_buf = io.BytesIO()
        plt.savefig(img_buf, format="png")
        img_buf.seek(0)

        plt.close()

        if self.conf["useCache"]:
            filepath = common.cache_manager.save(
                "background_contour", "contour1.png", self.conf
            )
            with open(filepath, "wb") as f:
                f.write(img_buf.getvalue())

        img_buf.seek(0)

        return self.contourToPixmap(img_buf)

    def checkCache(self, conf):
        params = ["backgroundColor", "wheelTextureColor", "seed"]

        for p in params:
            if not self.conf.get(p) == conf.get(p):
                return False
        return True

    def updatePixmap(self):
        self.setTexture(self.genContour())

    def loadPixmap(self):
        if self.conf["useCache"] and not self.conf["randomSeed"]:
            ok, filepath, conf = common.cache_manager.load(
                "background_contour", "contour1.png"
            )
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

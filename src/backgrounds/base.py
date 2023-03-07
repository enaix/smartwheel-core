from PyQt6.QtGui import QBrush


class Background(QBrush):
    def __init__(self, canvas=None):
        super(Background, self).__init__()
        self.canvas_obj = canvas


# Needs to be at the end of the file
#brushes = {}
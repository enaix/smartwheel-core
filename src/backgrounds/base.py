from PyQt6.QtGui import QBrush


class Background(QBrush):
    """
    Background object, inherited from QBrush. Please see Qt6 QBrush documentation

    Must contain brushes dict at the end of the file
    """

    def __init__(self, common_config=None, config=None, canvas=None, *args, **kwargs):
        super(Background, self).__init__(*args, **kwargs)
        self.common_config = common_config
        self.conf = config
        self.canvas = canvas


# Needs to be at the end of the file
# brushes = {}

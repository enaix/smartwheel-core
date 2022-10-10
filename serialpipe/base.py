from PyQt5.QtCore import QThread, QObject, QTimer, pyqtSlot
import time


class PRButton(QObject):
    """Press and release button"""
    def __init__(self, click_thresh, parent=None):
        """
        Initialize PRButton

        Parameters
        ----------
        click_thresh
            Doubleclick threshold in milliseconds
        parent
            QObject parent, default is None
        """
        super(PRButton, self).__init__(parent)

        self.arguments = [None, None, None]
        self.signals = [None, None, None]
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(click_thresh)
        self.timer.timeout.connect(self.pressTimeout)

        self.state = "up"
        self.buttonType = "pressReleaseButton"
        self.click_thresh = click_thresh

    def setupCallbacks(self, signals, arguments):
        """
        Connect signals to button actions

        Parameters
        ----------
        signals
            List of signals [button down, single click, double click]
            Each signal is pyqtSignal or None
        arguments
            List of arguments [button down, single click, double click]
            Each signal is some datatype or None
        """
        self.signals = signals
        self.arguments = arguments

    def press(self, down):
        """
        Press button event

        Parameters
        ----------
        down
            Is button pressed down
        """
        up = not down

        if self.state == "up" and down:  # Unpressed
            self.state = "down_pre"  # Button down
            self.timer.stop()
            if self.signals[0] is not None:
                self.signals[0].emit(self.arguments[0])

        elif self.state == "down_pre" and up:  # Pressed down and up (need to check if rotary is not activated)
            self.state = "click_pre"
            self.timer.stop()
            self.timer.start()

        elif self.state == "click_pre" and down:  # Single click and press down
            self.state = "double_pre"
            self.timer.stop()

        elif self.state == "double_pre" and up:  # double click
            self.state = "up"
            self.timer.stop()
            if self.signals[2] is not None:
                self.signals[2].emit(self.arguments[2])

        elif up:  # drop the state
            self.state = "up"

    @pyqtSlot()
    def pressTimeout(self):
        """
        Click timeout exceeded
        """
        if self.state == "click_pre":  # single click
            self.state = "up"
            if self.signals[1] is not None:
                self.signals[1].emit(self.arguments[1])


class ClickButton(QObject):
    """Simple click button without separate up and down events"""
    def __init__(self, click_thresh, parent=None):
        """
        Initialize ClickButton

        Parameters
        ----------
        click_thresh
            Doubleclick threshold in milliseconds
        parent
            QObject parent, default is None
        """
        super(ClickButton, self).__init__(parent)

        self.arguments = [None, None]
        self.signals = [None, None]
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(click_thresh)
        self.timer.timeout.connect(self.pressTimeout)

        self.state = "unpressed"
        self.buttonType = "clickButton"
        self.click_thresh = click_thresh

    def setupCallbacks(self, signals, arguments):
        """
        Connect signals to button actions

        Parameters
        ----------
        signals
            List of signals [single click, double click]
            Each signal is pyqtSignal or None
        arguments
            List of arguments [single click, double click]
            Each signal is some datatype or None
        """
        self.signals = signals
        self.arguments = arguments

    def press(self):
        """
        Press button event
        """
        if self.state == "unpressed":  # single click
            self.state = "double_pre"
            self.timer.stop()
            self.timer.start()

        elif self.state == "double_pre":  # double click
            self.state = "unpressed"
            self.timer.stop()
            if self.signals[1] is not None:
                self.signals[1].emit(self.arguments[1])

    @pyqtSlot()
    def pressTimeout(self):
        """
        Click timeout exceeded
        """
        if self.state == "double_pre":
            self.state = "unpressed"
            if self.signals[0] is not None:
                self.signals[0].emit(self.arguments[0])


class Rotary(QObject):
    """Simple rotary encoder with up and down events"""
    def __init__(self, prbutton, parent=None):
        """
        Initialize Rotary

        Parameters
        ----------
        prbutton
            Linked PRButton
        """
        super(Rotary, self).__init__(parent)

        self.btn = prbutton

        self.signals = [None]*6
        self.arguments = [None] * 6

    def setupCallbacks(self, signals, arguments):
        """
        Connect signals to encoder actions

        Parameters
        ----------
        signals
            List of signals [up, down, button hold + up, button hold + down, doubleclick + up, doubleclick + down]
            Each signal is pyqtSignal or None
        arguments
            List of arguments [...]
            Each signal is some datatype or None
        """
        self.signals = signals
        self.arguments = arguments
        
    def callSignal(self, i, up):
        """
        Call the specified signal
        
        Parameters
        ----------
        i
            Index of the clockwise (up) signal
        up
            Is the direction up
        """
        if i+1 > len(self.signals):
            return
        if up:
            if self.signals[i] is not None:
                self.signals[i].emit(self.arguments[0])
        else:
            if self.signals[i+1] is not None:
                self.signals[i+1].emit(self.arguments[1])

    def rotate(self, up):
        """
        Rotation event
        
        Parameters
        ----------
        up
            Is the direction up (up - clockwise)
        """
        down = not up
        if self.btn is None:  # No linked btn
            self.callSignal(0, up)

        elif self.btn.state == "up" or self.btn.state == "click_pre":  # Rotation up/down
            self.btn.state = "up"
            self.btn.timer.stop()
            self.callSignal(0, up)

        elif self.btn.state == "down_pre" or self.btn.state == "down":  # Click and scroll
            self.btn.state = "down"  # the next up event won't trigger anything
            self.btn.timer.stop()
            self.callSignal(2, up)

        elif self.btn.state == "double_pre" or self.btn.state == "double":
            self.btn.state = "double"  # the next up event won't trigger anything
            self.btn.timer.stop()
            self.callSignal(4, up)


class ConnPipe(QThread):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        pass

    def isDoubleClick(self, old_time, thresh):
        if time.process_time_ns() - old_time >= thresh:
            return True
        return False

    def __del__(self):
        self.wait()

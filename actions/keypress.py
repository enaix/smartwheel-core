from actions.baseaction import BaseAction
from pynput.keyboard import Key, KeyCode, Controller
import os

class Action(BaseAction):
    def __init__(self):
        self.keeb = Controller()

    def run(self, context):
        if context["type"] == "up":
            up = True
            down = False
        elif context["type"] == "down":
            up = False
            down = True
        else:
            up = True
            down = True
        if context["key_class"] == "special":
            if hasattr(Key, context["key"]):
                for _ in range(context["repeat"] + 1):
                    if down:
                        self.keeb.press(getattr(Key, context["key"]))
                    if up:
                        self.keeb.release(getattr(Key, context["key"]))
            else:
                print("Error: cannot parse Key.", context["key"], ". Please check pynput.Key class",sep="")
                print("Key context:", context)
                return False
        elif context["key_class"] == "regular":
            for _ in range(context["repeat"] + 1):
                if down:
                    self.keeb.press(context["key"])
                if up:
                    self.keeb.release(context["key"])
        elif context["key_class"] == "vk":
            for _ in range(context["repeat"] + 1):
                if down:
                    self.keeb.press(KeyCode.from_vk(int(context["key"], 16) + 0x200))
                if up:
                    self.keeb.release(KeyCode.from_vk(int(context["key"], 16) + 0x200))
        elif context["key_class"] == "xdotool":
            for _ in range(context["repeat"] + 1):
                if down:
                    os.system("xdotool keydown " + context["key"])
                if up:
                    os.system("xdotool keyup " + context["key"])
        else:
            return False
        return True

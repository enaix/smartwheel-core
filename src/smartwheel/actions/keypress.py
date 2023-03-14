import logging
import os

from pynput.keyboard import Controller, Key, KeyCode

from smartwheel.actions.baseaction import BaseAction


class Action(BaseAction):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.keeb = Controller()
        self.media_keys = {
            "play_pause": Key.media_play_pause,
            "next": Key.media_next,
            "previous": Key.media_previous,
            "down": Key.media_volume_down,
            "up": Key.media_volume_up,
            "mute": Key.media_volume_mute,
        }

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
                self.logger.warning(
                    "Error: cannot parse Key.",
                    context["key"],
                    ". Please check pynput.Key class",
                    sep="",
                )
                self.logger.info("Key context:", context)
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

        elif context["key_class"] == "media":
            key = self.media_keys.get(context["key"])
            if key is None:
                self.logger.warning("No such media key: " + context["key"])
                return False

            for _ in range(context["repeat"] + 1):
                if down:
                    self.keeb.press(key)
                if up:
                    self.keeb.release(key)
        else:
            return False
        return True

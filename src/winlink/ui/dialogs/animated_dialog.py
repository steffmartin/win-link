"""Short dialog transitions respecting the Windows animation preference."""

import ctypes
import os

from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtWidgets import QDialog


class AnimatedDialog(QDialog):
    def showEvent(self, event):
        super().showEvent(event)
        enabled = ctypes.c_int(0)
        if (
            os.name != "nt"
            or not ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0)
            or not enabled.value
        ):
            return
        previous = getattr(self, "_fade", None)
        if previous is not None:
            previous.stop()
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(120)
        self._fade.setStartValue(0.92)
        self._fade.setEndValue(1.0)
        self._fade.start()

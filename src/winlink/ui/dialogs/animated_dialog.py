"""Short dialog transitions respecting the Windows animation preference."""

import ctypes
import os

from PyQt6.QtCore import QPropertyAnimation, Qt
from PyQt6.QtWidgets import QDialog, QScrollArea, QVBoxLayout, QWidget


class AnimatedDialog(QDialog):
    def showEvent(self, event):
        from winlink.ui.icons import refresh_widget_icons

        refresh_widget_icons(self)
        if self.isWindow() and not getattr(self, "_scroll_ready", False) and self.layout():
            self._scroll_ready = True
            content = QWidget()
            content.setLayout(self.layout())
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setFrameShape(QScrollArea.Shape.NoFrame)
            area.setWidget(content)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(area)
            available = self.screen().availableGeometry()
            self.setMinimumSize(320, 180)
            self.resize(
                min(getattr(self, "preferred_width", 680), int(available.width() * 0.9)),
                min(content.sizeHint().height() + 40, int(available.height() * 0.9)),
            )
            self.setMaximumHeight(int(available.height() * 0.9))
            for label in self.findChildren(QWidget):
                if label.inherits("QLabel"):
                    label.setTextInteractionFlags(
                        label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse
                    )
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

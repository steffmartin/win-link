"""Page adapters reuse the production dialogs and their validation workflows."""

from typing import cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QScrollArea

from winlink.ui.dialogs import CreateJunctionDialog, HistoryDialog, SettingsDialog


class PageMixin:
    def done(self, result):
        if result == QDialog.DialogCode.Accepted:
            cast(QDialog, self).accepted.emit()
        else:
            cast(QDialog, self).rejected.emit()


def embed_page(dialog, stack):
    dialog.setWindowFlags(Qt.WindowType.Widget)
    dialog.setModal(False)
    dialog.setMinimumSize(0, 0)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setWidget(dialog)
    stack.addWidget(area)
    return area


class CreatePage(PageMixin, CreateJunctionDialog):
    pass


class HistoryPage(PageMixin, HistoryDialog):
    pass


class SettingsPage(PageMixin, SettingsDialog):
    pass

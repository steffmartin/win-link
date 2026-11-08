"""Virtualized history row actions; domain validation remains in HistoryDialog."""

from PyQt6.QtCore import QEvent, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionButton

from winlink.core.history import creation_was_undone
from winlink.core.models import OperationType
from winlink.ui.icons import symbol_icon
from winlink.ui.theme import ThemeColors


class HistoryActionDelegate(QStyledItemDelegate):
    requested = pyqtSignal(object, str)

    def available(self, index):
        record = index.model().get_operation(index)
        return bool(
            record
            and record.success
            and record.operation_type
            in (
                OperationType.CREATE_JUNCTION,
                OperationType.CREATE_SYMLINK,
                OperationType.CREATE_HARDLINK,
            )
            and not creation_was_undone(record, index.model().all_operations)
        )

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        color = option.palette.color(QPalette.ColorRole.ButtonText).name()
        for offset, text, icon in [(0, "Detalhes", "info"), (106, "Desfazer", "undo")]:
            if offset and not self.available(index):
                continue
            button = QStyleOptionButton()
            button.rect = QRect(option.rect.left() + 8 + offset, option.rect.top() + 12, 100, 38)
            button.text = text
            button.icon = symbol_icon(icon, color)
            button.iconSize = QSize(16, 16)
            button.state = QStyle.StateFlag.State_Enabled
            option.widget.style().drawControl(
                QStyle.ControlElement.CE_PushButton, button, painter, option.widget
            )

    def editorEvent(self, event, model, option, index):
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
        ):
            x = event.position().x() - option.rect.left()
            if 8 <= x <= 108:
                self.requested.emit(index, "details")
                return True
            if 114 <= x <= 214 and self.available(index):
                self.requested.emit(index, "undo")
                return True
        return False


class HistoryStatusDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        # The badge replaces the default text; model data remains plain for accessibility.
        rect = option.rect.adjusted(4, 4, -4, -4)
        painter.fillRect(rect, option.palette.base())
        text = str(index.data() or "")
        dark = option.palette.window().color().lightness() < 128
        colors = ThemeColors.DARK if dark else ThemeColors.LIGHT
        key = (
            "success"
            if text == "Sucesso"
            else "cancel" if text == "Cancelado" else "undone" if "desfeita" in text else "error"
        )
        foreground, background = {
            "success": (colors["success"], colors["success_container"]),
            "cancel": (colors["warning"], colors["warning_container"]),
            "undone": (colors["text_secondary"], colors["surface_variant"]),
            "error": (colors["error"], colors["error_container"]),
        }[key]
        width = min(rect.width() - 8, painter.fontMetrics().horizontalAdvance(text) + 42)
        badge = QRect(rect.left() + 4, rect.center().y() - 15, width, 30)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(badge, 6, 6)
        symbol_icon(
            (
                "check"
                if key == "success"
                else "undo" if key == "undone" else "warning" if key == "cancel" else "error"
            ),
            foreground.name(),
        ).paint(painter, QRect(badge.left() + 8, badge.top() + 7, 16, 16))
        painter.setPen(foreground)
        painter.drawText(badge.adjusted(30, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter, text)
        painter.restore()

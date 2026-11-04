"""Virtualized link cards using the same production proxy model as compact view."""

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPen
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate


class LinkCardDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(400, 116)

    def paint(self, painter, option, index):
        proxy = index.model()
        junction = proxy.sourceModel().get_junction(proxy.mapToSource(index))
        if junction is None:
            return
        painter.save()
        colors = option.palette
        rect = option.rect.adjusted(0, 6, -2, -6)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        painter.setBrush(colors.highlight() if selected else colors.alternateBase())
        painter.setPen(QPen(colors.mid().color(), 1))
        painter.drawRoundedRect(rect, 8, 8)
        foreground = colors.highlightedText().color() if selected else colors.text().color()
        painter.setPen(foreground)
        font = QFont(option.font)
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        left = rect.left() + 20
        width = max(80, rect.width() - 240)
        painter.drawText(
            QRect(left, rect.top() + 16, width, 24),
            Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(
                junction.target.name, Qt.TextElideMode.ElideMiddle, width
            ),
        )
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        model = proxy.sourceModel()
        creator = model._get_creator_display(junction.creator)
        size = model._format_size(junction.size_bytes)
        painter.drawText(
            QRect(left, rect.top() + 42, width, 20),
            Qt.AlignmentFlag.AlignVCenter,
            f"{creator} · {size}",
        )
        path = f"{junction.source}  →  {junction.target}"
        painter.drawText(
            QRect(left, rect.top() + 68, rect.width() - 40, 20),
            Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(path, Qt.TextElideMode.ElideMiddle, rect.width() - 40),
        )
        kind = model._get_type_display(junction.junction_type)
        if junction.junction_type.value == "SYMLINK":
            kind += " (diretório)" if junction.is_directory else " (arquivo)"
        right = QRect(rect.right() - 200, rect.top() + 16, 180, 22)
        painter.drawText(right, Qt.AlignmentFlag.AlignRight, kind)
        status = model._get_status_display(junction.status)
        if not selected:
            painter.setPen(
                QColor(
                    {"ACTIVE": "#16a34a", "BROKEN": "#d97706", "INACCESSIBLE": "#ef4444"}[
                        junction.status.value
                    ]
                )
            )
        painter.drawText(right.translated(0, 26), Qt.AlignmentFlag.AlignRight, status)
        if option.state & QStyle.StateFlag.State_HasFocus:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#3b82f6"), 2))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 8, 8)
        painter.restore()

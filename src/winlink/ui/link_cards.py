"""Virtualized link cards using the same production proxy model as compact view."""

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPen
from PyQt6.QtWidgets import QHeaderView, QListView, QStyle, QStyledItemDelegate

from winlink.ui.icons import symbol_icon


class LinkTableHeader(QHeaderView):
    """Share changes in available width while keeping columns user-resizable."""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.count() < 2:
            return
        minimum = self.minimumSectionSize()
        fixed = sum(self.sectionSize(column) for column in range(2, self.count()))
        previous = max(2 * minimum, event.oldSize().width() - fixed)
        available = max(2 * minimum, event.size().width() - fixed)
        delta = available - previous
        if not delta:
            return
        current = self.sectionSize(0) + self.sectionSize(1)
        total = max(2 * minimum, current + delta) if event.oldSize().isValid() else available
        first = max(
            minimum, min(total - minimum, (total + self.sectionSize(0) - self.sectionSize(1)) // 2)
        )
        self.resizeSection(0, first)
        self.resizeSection(1, total - first)


class LinkCardView(QListView):
    def __init__(self):
        super().__init__()
        self.setViewportMargins(0, 0, 8, 0)


class LinkCardDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(400, 120)

    def paint(self, painter, option, index):
        proxy = index.model()
        junction = proxy.sourceModel().get_junction(proxy.mapToSource(index))
        if junction is None:
            return
        painter.save()
        colors = option.palette
        rect = option.rect.adjusted(0, 6, -2, -6)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        dark = colors.window().color().lightness() < 128
        painter.setBrush(QColor("#1f2937" if dark else "#f9fafb"))
        painter.setPen(QPen(QColor("#3b82f6") if selected else colors.mid().color(), 1))
        painter.drawRoundedRect(rect, 8, 8)
        foreground = colors.text().color()
        painter.setPen(foreground)
        font = QFont(option.font)
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        dark = colors.window().color().lightness() < 128
        tile = QRect(rect.left() + 16, rect.top() + 26, 48, 48)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#172554" if dark else "#dbeafe"))
        painter.drawRoundedRect(tile, 12, 12)
        symbol_icon(
            "folder" if junction.is_directory else "file", "#60a5fa" if dark else "#2563eb"
        ).paint(painter, tile.adjusted(12, 12, -12, -12))
        painter.setPen(foreground)
        left = rect.left() + 80
        width = max(60, rect.width() - 300)
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
            QRect(left, rect.top() + 68, rect.width() - 112, 20),
            Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(
                path, Qt.TextElideMode.ElideMiddle, rect.width() - 112
            ),
        )
        kind = model._get_type_display(junction.junction_type)
        if junction.junction_type.value == "SYMLINK":
            kind += " (diretório)" if junction.is_directory else " (arquivo)"
        right = QRect(rect.right() - 214, rect.top() + 20, 164, 22)
        painter.drawText(right, Qt.AlignmentFlag.AlignRight, kind)
        status = {"ACTIVE": "Ativo", "BROKEN": "Quebrado", "INACCESSIBLE": "Inacessível"}[
            junction.status.value
        ]
        from winlink.ui.theme import junction_status_color

        tone = junction_status_color(junction.status).name()
        painter.setPen(QColor(tone))
        status_rect = right.translated(0, 26)
        painter.drawText(status_rect, Qt.AlignmentFlag.AlignRight, status)
        width = painter.fontMetrics().horizontalAdvance(status)
        from winlink.ui.icons import status_icon

        status_icon(junction.status, tone).paint(
            painter, QRect(status_rect.right() - width - 22, status_rect.top(), 16, 16)
        )
        symbol_icon("more", "#9ca3af").paint(
            painter, QRect(rect.right() - 32, rect.top() + 40, 20, 20)
        )
        if option.state & QStyle.StateFlag.State_HasFocus:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#3b82f6"), 2))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 8, 8)
        painter.restore()

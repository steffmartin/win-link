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
        available = self.width() - fixed
        if available < 2 * minimum:
            return
        current = self.sectionSize(0) + self.sectionSize(1)
        if current == available:
            return
        total = available
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

    @staticmethod
    def _fit_tags(tags, available_width, metrics):
        gap = 4
        widths = [min(160, metrics.horizontalAdvance(tag) + 16) for tag in tags]
        if sum(widths) + gap * max(0, len(widths) - 1) <= available_width:
            return list(zip(tags, widths, strict=True))

        for visible_count in range(len(tags), -1, -1):
            hidden_count = len(tags) - visible_count
            overflow = f"+{hidden_count}" if hidden_count else ""
            overflow_width = metrics.horizontalAdvance(overflow) + 16 if overflow else 0
            used = sum(widths[:visible_count]) + gap * max(0, visible_count - 1)
            if hidden_count and visible_count:
                used += gap
            if hidden_count:
                used += overflow_width
            if used <= available_width:
                fitted = list(zip(tags[:visible_count], widths[:visible_count], strict=True))
                if hidden_count:
                    fitted.append((overflow, overflow_width))
                return fitted
        return []

    @staticmethod
    def _tag_pill_rects(tag_pills, right_edge, y):
        rects = []
        for _, pill_width in reversed(tag_pills):
            rects.append(QRect(right_edge - pill_width + 1, y, pill_width, 18))
            right_edge -= pill_width + 4
        return list(reversed(rects))

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
        from winlink.ui.theme import ThemeColors

        theme = ThemeColors.DARK if dark else ThemeColors.LIGHT
        painter.setBrush(colors.base().color())
        painter.setPen(QPen(theme["primary"] if selected else colors.mid().color(), 1))
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
        painter.setBrush(theme["primary_container"])
        painter.drawRoundedRect(tile, 12, 12)
        symbol_icon("folder" if junction.is_directory else "file", theme["primary"].name()).paint(
            painter, tile.adjusted(12, 12, -12, -12)
        )
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
        path_width = rect.width() - 112
        tag_pills = []
        if junction.tags:
            metrics = painter.fontMetrics()
            available = max(0, rect.width() - 80 - 14 - 100 - 8)
            available = min(available, int(rect.width() * 0.45))
            tag_pills = self._fit_tags(junction.tags, available, metrics)
            tag_width = sum(width for _, width in tag_pills) + 4 * max(0, len(tag_pills) - 1)
            path_width = max(60, rect.width() - 80 - 14 - tag_width - 8)
        painter.drawText(
            QRect(left, rect.top() + 68, path_width, 20),
            Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(path, Qt.TextElideMode.ElideMiddle, path_width),
        )
        from winlink.ui.type_labels import link_type_label

        kind = link_type_label(junction.junction_type, junction.is_directory)
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
        if tag_pills:
            y = rect.top() + 69
            painter.setFont(option.font)
            for (tag, _), pill in zip(
                tag_pills, self._tag_pill_rects(tag_pills, status_rect.right(), y), strict=True
            ):
                painter.setPen(colors.mid().color())
                painter.setBrush(colors.alternateBase().color())
                painter.drawRoundedRect(pill, 8, 8)
                painter.setPen(foreground)
                text = painter.fontMetrics().elidedText(
                    tag, Qt.TextElideMode.ElideRight, max(1, pill.width() - 12)
                )
                painter.drawText(pill.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter, text)
        symbol_icon("more", theme["text_secondary"].name()).paint(
            painter, QRect(rect.right() - 32, rect.top() + 40, 20, 20)
        )
        if option.state & QStyle.StateFlag.State_HasFocus:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(theme["primary"], 2))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 8, 8)
        painter.restore()

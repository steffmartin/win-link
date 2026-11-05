"""Application artwork drawn with Qt; no runtime asset dependencies."""

from functools import lru_cache

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def application_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / 64, size / 64)
        painter.setPen(QPen(QColor("#0078D4"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawRoundedRect(QRectF(7, 17, 31, 22), 10, 10)
        painter.setPen(QPen(QColor("#50B5FF"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawRoundedRect(QRectF(26, 25, 31, 22), 10, 10)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


# Consistent 24-unit outline symbols, rendered at native and high-DPI sizes.
_SYMBOLS = {
    "folder": '<path d="M3 7V5h6l2 2h10v12H3z"/>',
    "file": '<path d="M6 3h8l4 4v14H6zM14 3v5h4"/>',
    "link": '<path d="m10 13 4-4M8 15l-2 2a4 4 0 0 1-5-5l5-5a4 4 0 0 1 6 0M16 9l2-2a4 4 0 0 1 5 5l-5 5a4 4 0 0 1-6 0" transform="translate(0 -1)"/>',
    "drive": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 14h18M7 17h.01M11 17h.01"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "settings": '<path d="m10 3-1 3-3 1-3 3 2 2-1 4 3 2 3-1 2 4 3-2 1-3 4-1 1-4-3-2-1-4-4 1z"/><circle cx="12" cy="12" r="3"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "filter": '<path d="M3 4h18l-7 8v7l-4 2v-9z"/>',
    "refresh": '<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',
    "home": '<path d="m3 11 9-8 9 8M5 9v12h5v-7h4v7h5V9"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 1v2M12 21v2M1 12h2M21 12h2M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2"/>',
    "moon": '<path d="M20 14A9 9 0 0 1 10 3a9 9 0 1 0 10 11z"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 5M12 17h.01"/>',
    "system": '<circle cx="8" cy="8" r="3"/><path d="M8 2v1M8 13v1M2 8h1M13 8h1M4 4l.5.5M12 4l-.5.5M4 12l.5-.5M22 16a6 6 0 0 1-7-7 6.5 6.5 0 1 0 7 7Z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    "back": '<path d="M20 12H4m6-6-6 6 6 6"/>',
    "undo": '<path d="m8 4-5 5 5 5M3 9h10a7 7 0 0 1 7 7v3"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m7 12 3 3 7-7"/>',
    "error": '<circle cx="12" cy="12" r="9"/><path d="m8 8 8 8m0-8-8 8"/>',
    "warning": '<path d="m12 3 10 18H2zM12 9v5M12 17h.01"/>',
    "shield": '<path d="M12 3 3 6v6c0 5 9 9 9 9s9-4 9-9V6zM12 8v5M12 16h.01"/>',
    "trash": '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
    "save": '<path d="M4 3h14l3 3v15H3V3h1M7 3v6h10V3M7 21v-8h10v8"/>',
    "external": '<path d="M14 3h7v7m0-7L10 14M10 3H3v18h18v-7"/>',
    "more": '<circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>',
    "keyboard": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M6 9h.01M10 9h.01M14 9h.01M18 9h.01M6 12h.01M10 12h.01M14 12h.01M18 12h.01M7 16h10"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
}


@lru_cache(maxsize=128)
def symbol_icon(name: str, color: str = "#64748b") -> QIcon:
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtSvg import QSvgRenderer

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        + _SYMBOLS[name]
        + "</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    icon = QIcon()
    for size in (16, 18, 20, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def set_button_icon(button, name: str, size: int = 18):
    from PyQt6.QtCore import QSize

    button.setProperty("symbol", name)
    button.setIconSize(QSize(size, size))
    button.setIcon(symbol_icon(name))


def refresh_widget_icons(root):
    from PyQt6.QtWidgets import QAbstractButton, QListWidget

    dark = root.palette().window().color().lightness() < 128
    color = "#d1d5db" if dark else "#4b5563"
    for button in root.findChildren(QAbstractButton):
        name = button.property("symbol")
        if name:
            tone = (
                "#ffffff"
                if button.property("primary")
                else ("#f87171" if dark else "#dc2626") if button.property("danger") else color
            )
            button.setIcon(symbol_icon(name, tone))
    for navigation in root.findChildren(QListWidget, "navigation"):
        for index, name in enumerate(("drive", "plus", "clock", "settings")):
            navigation.item(index).setIcon(symbol_icon(name, color))

"""Application artwork drawn with Qt; no runtime asset dependencies."""

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

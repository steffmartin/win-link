"""Generate the Inno Setup artwork with the same mark as the application."""

from pathlib import Path

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter
from PyQt6.QtWidgets import QApplication

from winlink.ui.icons import application_icon


def create_wizard_artwork():
    app = QApplication.instance() or QApplication([])
    assert app is not None
    icon = application_icon()
    output = Path(__file__).parent
    for name, width, height, size in (
        ("wizard-side", 164, 314, 104),
        ("wizard-header", 55, 55, 46),
    ):
        image = QImage(width, height, QImage.Format.Format_RGB32)
        painter = QPainter(image)
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor("#0B5058"))
        gradient.setColorAt(1, QColor("#126E78"))
        painter.fillRect(image.rect(), gradient)
        icon.paint(painter, QRect((width - size) // 2, (height - size) // 2, size, size))
        painter.end()
        if not image.save(str(output / f"{name}.bmp")):
            raise OSError(f"Could not save installer artwork: {name}")


if __name__ == "__main__":
    create_wizard_artwork()

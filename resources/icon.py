"""Generate the Windows multi-resolution icon using the application artwork."""

import struct
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
from PyQt6.QtWidgets import QApplication

from winlink.ui.icons import application_icon


def create_icon():
    app = QApplication.instance() or QApplication([])  # Keep Qt alive while rendering.
    assert app is not None
    icon = application_icon()
    entries, payloads = [], []
    sizes = (16, 32, 48, 64, 128, 256)
    offset = 6 + 16 * len(sizes)
    for size in sizes:
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        icon.pixmap(size, size).save(buffer, "PNG")
        payload = bytes(data)
        entries.append(
            struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(payload), offset)
        )
        payloads.append(payload)
        offset += len(payload)
    path = Path(__file__).with_name("winlink.ico")
    path.write_bytes(struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries + payloads))
    return path


if __name__ == "__main__":
    print(create_icon())

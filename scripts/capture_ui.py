"""Capture actual Qt pages with real links in an isolated temporary directory.

Usage: python scripts/capture_ui.py [output-directory]
Set QT_SCALE_FACTOR=2 in a fresh process to inspect high DPI.
"""

import os
import sys
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from winlink.core.config import AppSettings, save_settings
from winlink.core.history import HistoryManager
from winlink.core.models import Junction, JunctionType, OperationType
from winlink.core.operations import create_hard_link, create_junction
from winlink.ui.dialogs.properties_dialog import PropertiesDialog
from winlink.ui.main_window import MainWindow

app = QApplication([])
with tempfile.TemporaryDirectory(prefix="winlink-ui-") as tmp:
    root = Path(tmp)
    os.environ["APPDATA"] = str(root / "appdata")
    data = root / "Dados"
    data.mkdir()
    (data / "arquivo.txt").write_text("Dados reais para validação isolada", encoding="utf-8")
    links = root / "Links"
    links.mkdir()
    assert create_junction(data, links / "Projetos")
    assert create_hard_link(data / "arquivo.txt", links / "outro-nome.txt")
    save_settings(AppSettings(scan_directories=[str(links)], remember_window_size=False))
    manager = HistoryManager()
    manager.add_operation(OperationType.CREATE_JUNCTION, data, links / "Projetos")
    manager.add_operation(
        OperationType.CREATE_HARDLINK, data / "arquivo.txt", links / "outro-nome.txt"
    )
    window = MainWindow()
    window.show()
    while window.scan_worker and window.scan_worker.isRunning():
        app.processEvents()
    app.processEvents()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build/ui-review")
    out.mkdir(parents=True, exist_ok=True)
    for theme in ["light", "dark"]:
        window.quick_theme.setCurrentIndex(window.quick_theme.findData(theme))
        for index, name in enumerate(["lista", "criacao", "historico", "configuracoes"]):
            window.navigate(index)
            window.resize(1280, 800)
            app.processEvents()
            window.grab().save(str(out / f"{name}-{theme}.png"))
            window.resize(760, 400)
            app.processEvents()
            window.grab().save(str(out / f"{name}-{theme}-small.png"))
            if index in (1, 3):
                area = window.pages.currentWidget()
                area.verticalScrollBar().setValue(area.verticalScrollBar().maximum())
                app.processEvents()
                window.grab().save(str(out / f"{name}-{theme}-small-bottom.png"))
                area.verticalScrollBar().setValue(0)
    junction = Junction(source=data, target=links / "Projetos", junction_type=JunctionType.JUNCTION)
    dialog = PropertiesDialog(junction, window, window.history_manager)
    dialog.show()
    app.processEvents()
    dialog.grab().save(str(out / "propriedades-dark.png"))
    dialog.close()
    window.close()
    app.processEvents()
    (links / "Projetos").rmdir()
print(out.resolve())

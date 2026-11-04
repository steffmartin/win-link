"""Capture actual Qt pages with real links in an isolated temporary directory.

Usage: python scripts/capture_ui.py [output-directory]
Set QT_SCALE_FACTOR=2 in a fresh process to inspect high DPI.
"""

import os
import sys
import tempfile
from pathlib import Path

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QScrollArea

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
            QTest.qWait(30)
            window.grab().save(str(out / f"{name}-{theme}.png"))
            window.resize(760, 400)
            app.processEvents()
            QTest.qWait(30)
            assert window.size().width() == 760 and window.size().height() == 400, window.size()
            window.grab().save(str(out / f"{name}-{theme}-small.png"))
            if index in (1, 3):
                area = window.pages.currentWidget()
                area.verticalScrollBar().setValue(area.verticalScrollBar().maximum())
                app.processEvents()
                window.grab().save(str(out / f"{name}-{theme}-small-bottom.png"))
                area.verticalScrollBar().setValue(0)

    from winlink.ui.dialogs.preview_dialog import PreviewDialog
    from winlink.ui.dialogs.progress_dialog import ProgressDialog
    from winlink.ui.dialogs.undo_dialog import UndoDialog

    for theme in ["light", "dark"]:
        window.quick_theme.setCurrentIndex(window.quick_theme.findData(theme))
        window.resize(1280, 800)
        junction = Junction(
            source=data, target=links / "Projetos", junction_type=JunctionType.JUNCTION
        )
        dialogs = [
            ("propriedades", PropertiesDialog(junction, window, window.history_manager)),
            ("previa", PreviewDialog(links / "Novo", data, window, JunctionType.JUNCTION)),
            ("reversao", UndoDialog(data, links / "Projetos", window)),
            ("progresso", ProgressDialog("Operação em Andamento", window)),
        ]
        for name, dialog in dialogs:
            dialog.show()
            QTest.qWait(40)
            dialog.grab().save(str(out / f"{name}-{theme}.png"))
            dialog.resize(520, 300)
            QTest.qWait(30)
            area = dialog.findChild(QScrollArea)
            if area:
                area.verticalScrollBar().setValue(area.verticalScrollBar().maximum())
            QTest.qWait(30)
            dialog.grab().save(str(out / f"{name}-{theme}-small-bottom.png"))
            if name == "progresso":
                dialog.set_operation_finished(
                    False, "Falha de teste para revisão visual; nenhum arquivo foi alterado."
                )
            dialog.close()

    # Record filter and About dialogs through the real application actions.
    def capture_modal(name):
        from PyQt6.QtCore import QTimer

        def capture():
            dialog = app.activeModalWidget()
            if dialog:
                dialog.grab().save(str(out / f"{name}-dark.png"))
                dialog.reject()

        QTimer.singleShot(100, capture)

    capture_modal("filtros")
    window.edit_filters()
    capture_modal("sobre")
    window.show_about()
    window.close()
    app.processEvents()
    (links / "Projetos").rmdir()
print(out.resolve())

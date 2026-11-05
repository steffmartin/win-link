"""Regressions for the isolated fixes in 0.1.1."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QFileDialog, QScrollArea

from winlink.core.config import AppSettings, get_settings, save_settings, settings_path
from winlink.core.models import Junction, JunctionType
from winlink.ui.dialogs.create_junction_dialog import CreateJunctionDialog
from winlink.ui.dialogs.preview_dialog import build_preview
from winlink.ui.dialogs.properties_dialog import PropertiesDialog
from winlink.ui.dialogs.settings_dialog import SettingsDialog
from winlink.ui.main_window import MainWindow


def test_default_scan_uses_current_home_and_preserves_saved_preferences(
    monkeypatch, tmp_path, qtbot
):
    home = tmp_path / "different-profile"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    assert AppSettings().scan_directories == [str(home)]
    saved = AppSettings(scan_directories=[str(tmp_path / "custom")])
    save_settings(saved)
    before = settings_path().read_bytes()
    dialog = SettingsDialog(saved)
    qtbot.addWidget(dialog)
    dialog.restore_defaults()
    assert dialog.scan_list.item(0).text() == str(home)
    assert dialog.scan_list.count() == 1
    assert settings_path().read_bytes() == before
    assert get_settings().scan_directories == saved.scan_directories
    dialog.discard_changes()
    assert dialog.scan_list.item(0).text() == saved.scan_directories[0]


@pytest.mark.parametrize("field", ["source", "target"])
@pytest.mark.parametrize("file", [False, True])
def test_browse_reuses_selection_and_cancel_preserves_it(qtbot, monkeypatch, tmp_path, field, file):
    dialog = CreateJunctionDialog()
    qtbot.addWidget(dialog)
    if file:
        dialog.select_type(2, False)
    selected = tmp_path / "chosen.txt" if file else tmp_path
    edit = getattr(dialog, field + "_edit")
    edit.setText(str(selected))
    picker = Mock(return_value=("", "") if file else "")
    method = (
        ("getOpenFileName" if field == "source" else "getSaveFileName")
        if file
        else "getExistingDirectory"
    )
    monkeypatch.setattr(QFileDialog, method, picker)
    getattr(dialog, "browse_" + field)()
    assert picker.call_args.args[2] == str(selected)
    assert edit.text() == str(selected)
    assert dialog.browse_start(str(tmp_path / "new" / "nested")) == str(tmp_path)


@pytest.mark.parametrize(
    "source_exists,target_exists", [(True, False), (False, False), (False, True), (True, True)]
)
def test_preview_describes_both_paths_once(monkeypatch, tmp_path, source_exists, target_exists):
    from winlink.core import file_ops, process_manager

    source, target = tmp_path / "physical", tmp_path / "access"
    if source_exists:
        source.mkdir()
    if target_exists:
        target.mkdir()
        (target / "payload.txt").write_text("preserve")
    monkeypatch.setattr(process_manager, "get_processes_using_directory", lambda path: [])
    monkeypatch.setattr(file_ops, "get_available_disk_space", lambda path: 1024 * 1024)
    text, valid = build_preview(target, source)
    assert valid
    assert text.count("Criar junção:") == 1
    assert (f"Local dos dados já existente: {source}" in text) == source_exists
    assert (f"Criar local dos dados: {source}" in text) == (not source_exists)
    assert ("Copiar arquivos de" in text) == target_exists
    if target_exists:
        assert f"Copiar arquivos de {target}" in text
        assert f"para {source}" in text
        assert (target / "payload.txt").read_text() == "preserve"
    assert source.exists() == source_exists


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=False))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    result = MainWindow()
    qtbot.addWidget(result)
    result.show()
    return result


def test_double_click_opens_properties_once_and_enter_still_works(
    window, qtbot, monkeypatch, tmp_path
):
    window.junction_model.set_junctions(
        [
            Junction(
                junction_type=JunctionType.JUNCTION,
                source=tmp_path / "data",
                target=tmp_path / "link",
            )
        ]
    )
    window.resize(1280, 800)
    callback = Mock()
    monkeypatch.setattr(window, "show_properties", callback)
    qtbot.wait(30)
    view = window.card_view
    index = window.filter_model.index(0, 0)
    view.scrollTo(index)
    point = view.visualRect(index).topLeft() + QPoint(100, 30)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=point)
    qtbot.mouseDClick(view.viewport(), Qt.MouseButton.LeftButton, pos=point)
    assert callback.call_count == 1
    view.setFocus()
    qtbot.keyClick(view, Qt.Key.Key_Return)
    assert callback.call_count == 2
    assert not window.table_view.verticalHeader().isVisible()
    assert window.table_view.verticalHeader().defaultSectionSize() < 48


def test_navigation_distinguishes_mouse_and_keyboard_focus(window, qtbot):
    nav = window.navigation
    qtbot.mouseClick(
        nav.viewport(), Qt.MouseButton.LeftButton, pos=nav.visualItemRect(nav.item(1)).center()
    )
    assert not nav.keyboard_focus
    qtbot.keyClick(nav, Qt.Key.Key_Down)
    assert nav.keyboard_focus
    assert nav.currentRow() == 2


@pytest.mark.parametrize("size", [(1280, 800), (520, 300)])
def test_properties_long_unbroken_paths_stay_inside_viewport(qtbot, monkeypatch, tmp_path, size):
    # Collecting real statistics is covered elsewhere; this test isolates layout.
    monkeypatch.setattr(PropertiesDialog, "load_junction_data", lambda self: None)
    dialog = PropertiesDialog(
        Junction(
            junction_type=JunctionType.JUNCTION, source=tmp_path, target=tmp_path / ("a" * 200)
        )
    )
    qtbot.addWidget(dialog)
    value = str(tmp_path / ("x" * 200) / ("y" * 200))
    dialog.source_label.setPlainText(value)
    dialog.target_label.setPlainText(value)
    dialog.show()
    dialog.resize(*size)
    qtbot.wait(30)
    area = dialog.findChild(QScrollArea)
    assert area.horizontalScrollBar().maximum() == 0
    for label in [dialog.source_label, dialog.target_label]:
        assert label.toPlainText() == value
        assert label.isReadOnly()
        label.selectAll()
        assert label.textCursor().selectedText() == value
        assert label.horizontalScrollBar().maximum() == 0
    area.ensureWidgetVisible(dialog.undo_btn)
    qtbot.wait(20)
    position = dialog.undo_btn.mapTo(area.viewport(), QPoint())
    assert position.y() >= 0
    assert position.y() + dialog.undo_btn.height() <= area.viewport().height()


def test_closing_window_destroys_theme_timer(qtbot, monkeypatch, tmp_path):
    from PyQt6 import sip

    save_settings(AppSettings(scan_directories=[str(tmp_path)]))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    window = MainWindow()
    manager = window.theme_manager
    timer = manager._system_timer
    assert timer.isActive()
    with qtbot.waitSignal(manager.destroyed, timeout=1000):
        window.deleteLater()
    assert sip.isdeleted(manager)
    assert sip.isdeleted(timer)

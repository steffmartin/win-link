"""Redesign integration regressions; all application/filesystem data is isolated."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QMessageBox, QScrollArea

from winlink.core.config import AppSettings, get_settings, save_settings, settings_path
from winlink.core.history import HistoryManager, creation_was_undone
from winlink.core.models import Junction, JunctionType, OperationRecord, OperationType
from winlink.ui.main_window import MainWindow
from winlink.ui.dialogs.settings_dialog import SettingsDialog
from winlink.ui.dialogs.history_dialog import HistoryDialog


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=False))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    result = MainWindow()
    qtbot.addWidget(result)
    result.show()
    return result


def test_legacy_config_roundtrip_preserves_storage(tmp_path):
    settings_path().parent.mkdir(parents=True, exist_ok=True)
    settings_path().write_text(
        '{"theme_mode":"dark","history_file":"D:/custom/history.json","show_notifications":false}'
    )
    settings = get_settings()
    assert settings.default_link_type == "junction"
    save_settings(settings)
    loaded = get_settings()
    assert loaded.history_file == Path("D:/custom/history.json")
    assert loaded.theme_mode == "dark" and not loaded.show_notifications


@pytest.mark.parametrize(
    "preference,index,file",
    [
        ("junction", 0, False),
        ("symlink_dir", 1, False),
        ("symlink_file", 1, True),
        ("hardlink", 2, False),
    ],
)
def test_default_type_reaches_creation_page(window, preference, index, file):
    window.settings.default_link_type = preference
    window.on_new_junction()
    assert window.pages.currentIndex() == 1
    assert window.create_page.type_combo.currentIndex() == index
    assert window.create_page.file_symlink.isChecked() == file
    assert window.create_page.is_directory_link() is (
        preference not in ("symlink_file", "hardlink")
    )


def test_settings_restore_discard_and_save_are_transactional(qtbot, tmp_path):
    settings = AppSettings(
        theme_mode="dark",
        default_link_type="hardlink",
        scan_directories=[str(tmp_path)],
        history_file=tmp_path / "custom.json",
    )
    save_settings(settings)
    original = settings_path().read_bytes()
    dialog = SettingsDialog(settings)
    qtbot.addWidget(dialog)
    dialog.restore_defaults()
    assert dialog.theme_combo.currentData() == "auto"
    assert settings_path().read_bytes() == original
    assert settings.theme_mode == "dark"
    dialog.discard_changes()
    assert dialog.theme_combo.currentData() == "dark"
    dialog.restore_defaults()
    dialog.save_settings()
    assert get_settings().theme_mode == "auto"
    assert get_settings().history_file == tmp_path / "custom.json"
    assert get_settings().confirm_before_destructive


def test_settings_save_failure_keeps_existing_data(qtbot, monkeypatch, tmp_path):
    from winlink.ui.dialogs import settings_dialog

    settings = AppSettings(theme_mode="dark")
    save_settings(settings)
    original = settings_path().read_bytes()
    dialog = SettingsDialog(settings)
    qtbot.addWidget(dialog)
    dialog.theme_combo.setCurrentIndex(dialog.theme_combo.findData("light"))
    monkeypatch.setattr(settings_dialog, "save_settings", Mock(side_effect=OSError("denied")))
    monkeypatch.setattr(QMessageBox, "critical", Mock())
    dialog.save_settings()
    assert settings.theme_mode == "dark"
    assert settings_path().read_bytes() == original


def test_pages_navigation_reentry_and_keyboard(window, qtbot):
    window.activateWindow()
    window.setFocus()
    qtbot.wait(50)
    qtbot.keyClick(window, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 2
    qtbot.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 1
    window._operation_active = True
    window.navigation.setCurrentRow(3)
    assert window.pages.currentIndex() == 1
    assert window.navigation.currentRow() == 1
    window._operation_active = False
    qtbot.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 0
    assert window.search_edit.hasFocus()


def test_symlink_file_and_directory_filter(window, tmp_path):
    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / str(i),
                target=tmp_path / f"link{i}",
                junction_type=JunctionType.SYMLINK,
                is_directory=directory,
            )
            for i, directory in enumerate([True, False])
        ]
    )
    window.type_filter.setCurrentIndex(4)
    assert window.filter_model.rowCount() == 1
    window.type_filter.setCurrentIndex(2)
    assert window.filter_model.rowCount() == 1
    window.clear_filters()
    assert window.filter_model.rowCount() == 2


@pytest.mark.parametrize("accept", [False, True])
def test_filters_use_draft(window, accept):
    def edit():
        dialog = window.findChild(QDialog)
        # Embedded pages are QDialogs too; pick the visible modal dialog.
        from PyQt6.QtWidgets import QApplication

        dialog = QApplication.activeModalWidget()
        dialog.findChildren(QComboBox)[0].setCurrentIndex(2)
        dialog.accept() if accept else dialog.reject()

    QTimer.singleShot(20, edit)
    window.edit_filters()
    assert window.status_filter.currentIndex() == (2 if accept else 0)


def test_history_combines_result_and_removes_custom_date_controls(qtbot, tmp_path):
    manager = HistoryManager(tmp_path / "history.json")
    records = [
        OperationRecord(
            operation_type=OperationType.CREATE_JUNCTION,
            timestamp=datetime(2026, 1, 2, 23, 59),
            success=True,
        ),
        OperationRecord(
            operation_type=OperationType.CREATE_JUNCTION,
            timestamp=datetime(2026, 1, 3),
            success=False,
        ),
    ]
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    assert [dialog.date_combo.itemText(i) for i in range(dialog.date_combo.count())] == [
        "Todos",
        "Hoje",
        "Última semana",
        "Último mês",
    ]
    assert not hasattr(dialog, "from_date")
    assert not hasattr(dialog, "to_date")
    dialog.result_combo.setCurrentText("Sucesso")
    dialog.apply_filters(records)
    assert dialog.table_model.rowCount() == 1
    assert "1 de 2" in dialog.total_label.text()
    assert dialog.clear_filter_btn.text() == "Limpar"
    assert dialog.clear_history_btn.text() == "Apagar histórico"


def test_legacy_undone_creation_cannot_be_repeated(qtbot, monkeypatch, tmp_path):
    manager = HistoryManager(tmp_path / "history.json")
    creation = OperationRecord(
        operation_type=OperationType.CREATE_JUNCTION,
        source=tmp_path / "data",
        target=tmp_path / "link",
        timestamp=datetime(2026, 1, 1),
    )
    undo = OperationRecord(
        operation_type=OperationType.UNDO_OPERATION,
        source=creation.source,
        target=creation.target,
        timestamp=datetime(2026, 1, 2),
    )
    records = [undo, creation]
    assert creation_was_undone(creation, records)
    manager._save_history([record.model_dump() for record in [creation, undo]])
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    dialog.table_view.setCurrentIndex(dialog.table_model.index(1, 0))
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    with qtbot.assertNotEmitted(dialog.undo_requested):
        dialog.undo_selected()
    assert dialog.table_model.data(dialog.table_model.index(1, 3)) == "Criação desfeita"


def test_small_window_pages_can_scroll_to_last_control(window, qtbot):
    window.resize(760, 400)
    for index, button in [(1, window.create_page.create_btn), (3, window.settings_page.save_btn)]:
        window.navigate(index)
        qtbot.wait(10)
        area = window.pages.currentWidget()
        assert isinstance(area, QScrollArea)
        area.ensureWidgetVisible(button)
        qtbot.wait(10)
        assert (
            area.viewport()
            .rect()
            .intersects(
                button.rect().translated(button.mapTo(area.viewport(), button.rect().topLeft()))
            )
        )


def test_quick_theme_persists_auto_and_manual(window, monkeypatch):
    window.quick_theme.setCurrentIndex(window.quick_theme.findData("dark"))
    assert get_settings().theme_mode == "dark"
    window.quick_theme.setCurrentIndex(window.quick_theme.findData("auto"))
    monkeypatch.setattr(window.theme_manager, "get_system_theme", lambda: "light")
    window.theme_manager.refresh_system_theme()
    assert window.theme_manager.current_theme == "light"
    assert get_settings().theme_mode == "auto"


def test_history_detects_replaced_junction_even_same_destination(qtbot, monkeypatch, tmp_path):
    from winlink.core.operations import create_junction

    data, link, old = tmp_path / "data", tmp_path / "link", tmp_path / "old"
    data.mkdir()
    assert create_junction(data, link)
    manager = HistoryManager(tmp_path / "history.json")
    assert manager.add_operation(OperationType.CREATE_JUNCTION, data, link)
    record = manager.get_history()[0]
    assert record.metadata["link_identity"]
    link.rename(old)
    try:
        assert create_junction(data, link)
        dialog = HistoryDialog(manager)
        qtbot.addWidget(dialog)
        dialog.table_view.setCurrentIndex(dialog.table_model.index(0, 0))
        warning = Mock()
        monkeypatch.setattr(QMessageBox, "warning", warning)
        with qtbot.assertNotEmitted(dialog.undo_requested):
            dialog.undo_selected()
        warning.assert_called_once()
        assert link.is_junction()
    finally:
        if link.is_junction():
            link.rmdir()
        old.rmdir()


def test_failed_scan_preserves_last_list(window, tmp_path):
    from winlink.core.models import ScanResult

    junction = Junction(
        source=tmp_path / "data", target=tmp_path / "link", junction_type=JunctionType.JUNCTION
    )
    window.junction_model.set_junctions([junction])
    window.on_scan_finished(
        ScanResult(
            errors=["Acesso negado"], excluded_directories=list(window.discovery_exclusions())
        )
    )
    assert window.junction_model.rowCount() == 1
    assert "preservada" in window.scan_notice.text()
    window.on_scan_finished(ScanResult(excluded_directories=list(window.discovery_exclusions())))
    assert window.junction_model.rowCount() == 0
    assert window.scan_notice.isHidden()


def test_progress_escape_requests_cooperative_cancel(qtbot):
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    dialog = ProgressDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    with qtbot.waitSignal(dialog.cancellation_requested):
        qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.isVisible()
    assert not dialog.cancel_btn.isEnabled()
    dialog.set_operation_finished(False, "Operação cancelada")
    assert dialog.status_label.text().startswith("Cancelado")
    qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert not dialog.isVisible()


def test_new_creation_page_runs_real_preview_and_junction(window, qtbot, monkeypatch, tmp_path):
    from winlink.ui.dialogs.preview_dialog import PreviewDialog
    from winlink.ui.dialogs.progress_dialog import ProgressDialog
    from PyQt6.QtWidgets import QApplication

    source, target = tmp_path / "data", tmp_path / "new-link"
    source.mkdir()
    (source / "important.txt").write_text("preserve")
    for name in ["warning", "information", "critical"]:
        monkeypatch.setattr(QMessageBox, name, Mock(return_value=QMessageBox.StandardButton.Yes))
    window.navigate(1)
    page = window.create_page
    page.source_edit.setText(str(source))
    page.target_edit.setText(str(target))
    timer = QTimer()

    def confirm():
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, PreviewDialog) and dialog.confirm_btn.isEnabled():
            timer.stop()
            dialog.confirm_btn.click()

    timer.timeout.connect(confirm)
    timer.start(10)
    try:
        page.create_btn.click()
        assert target.is_junction()
        assert (target / "important.txt").read_text() == "preserve"
        assert window.history_manager.get_history()[0].success
        assert window.history_manager.get_history()[0].metadata["link_identity"]
    finally:
        timer.stop()
        for widget in window.findChildren(ProgressDialog):
            widget.set_operation_finished(True)
            widget.close()
        if target.is_junction():
            target.rmdir()


def test_broken_directory_remove_only_checks_reference(tmp_path):
    from winlink.core.operations import create_junction, verify_directory_link_reference

    source, target, moved = tmp_path / "source", tmp_path / "link", tmp_path / "moved"
    source.mkdir()
    (source / "keep.txt").write_text("keep")
    assert create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    try:
        source.rename(moved)
        assert verify_directory_link_reference(junction)
        changed = Junction(
            source=tmp_path / "different", target=target, junction_type=JunctionType.JUNCTION
        )
        assert not verify_directory_link_reference(changed)
        assert (moved / "keep.txt").read_text() == "keep"
    finally:
        target.rmdir()


def test_properties_reversal_request_preserves_selection_until_confirmed(qtbot, tmp_path):
    from winlink.ui.dialogs.properties_dialog import PropertiesDialog

    data = tmp_path / "data"
    data.mkdir()
    junction = Junction(source=data, target=tmp_path / "link", junction_type=JunctionType.JUNCTION)
    dialog = PropertiesDialog(junction)
    qtbot.addWidget(dialog)
    dialog.show()
    with qtbot.waitSignal(dialog.undo_requested):
        dialog.undo_btn.click()
    assert dialog.isVisible()
    assert dialog.junction == junction


def test_stale_scan_cannot_restore_newly_excluded_links(window, tmp_path, monkeypatch):
    from winlink.core.cache import CacheManager
    from winlink.core.models import ScanResult

    excluded = tmp_path / "excluded"
    junction = Junction(
        source=tmp_path / "data",
        target=excluded / "link",
        junction_type=JunctionType.JUNCTION,
    )
    previous = list(window.discovery_exclusions())
    window.junction_model.set_junctions([junction])
    window.settings.scan_excluded_directories = [str(excluded)]
    window.settings_saved()
    assert window.junction_model.rowCount() == 0

    def unexpected_save(*args):
        pytest.fail("stale scan must not replace cache")

    monkeypatch.setattr(CacheManager, "save", unexpected_save)
    window.on_scan_finished(ScanResult(junctions=[junction], excluded_directories=previous))
    assert window.junction_model.rowCount() == 0

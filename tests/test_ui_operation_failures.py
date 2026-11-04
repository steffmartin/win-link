"""Regression tests for operation failures at the UI boundary."""

from unittest.mock import Mock

import pytest

from winlink.core import file_ops, operations, validators
from winlink.core.models import ValidationResult
from winlink.ui import main_window


@pytest.mark.parametrize("failed_step", ["copy", "create"])
def test_creation_failure_is_not_reported_as_success(qtbot, monkeypatch, tmp_path, failed_step):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    original = target / "original.txt"
    original.write_text("preserve me")
    monkeypatch.setattr(
        validators, "validate_junction_creation", lambda *a: ValidationResult(is_valid=True)
    )
    copy = Mock(return_value=failed_step != "copy")
    delete = Mock(return_value=failed_step != "delete")
    create = Mock(return_value=False)
    monkeypatch.setattr(file_ops, "copy_directory_with_metadata", copy)
    monkeypatch.setattr(file_ops, "delete_directory", delete)
    monkeypatch.setattr(operations, "create_junction", create)
    progress = Mock()
    monkeypatch.setattr(main_window, "ProgressDialog", Mock(return_value=progress))
    messages = Mock()
    monkeypatch.setattr(main_window, "QMessageBox", messages)
    window = Mock()

    main_window.MainWindow.create_link(window, target, source, main_window.JunctionType.JUNCTION)

    assert original.read_text() == "preserve me"
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False
    messages.information.assert_not_called()
    window.start_scan.assert_not_called()
    if failed_step == "copy":
        delete.assert_not_called()
        create.assert_not_called()


def test_refresh_does_not_replace_running_scanner():
    window = Mock()
    window.scan_worker.isRunning.return_value = True
    worker = window.scan_worker
    main_window.MainWindow.start_scan(window)
    assert window.scan_worker is worker
    window.status_bar.showMessage.assert_not_called()


def test_close_waits_for_running_scanner():
    window = Mock()
    window.scan_worker.isRunning.return_value = True
    event = Mock()
    main_window.MainWindow.closeEvent(window, event)
    event.ignore.assert_called_once()
    event.accept.assert_not_called()


def test_window_exposes_type_filter_and_sorting(qtbot, monkeypatch, tmp_path):
    from winlink.core.config import AppSettings
    from winlink.core.models import Junction, JunctionType

    monkeypatch.setattr(main_window.MainWindow, "start_scan", lambda self: None)
    monkeypatch.setattr(main_window, "get_settings", lambda: AppSettings())
    monkeypatch.setattr(main_window, "HistoryManager", Mock())
    window = main_window.MainWindow()
    qtbot.addWidget(window)
    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / "a", target=tmp_path / "b", junction_type=JunctionType.JUNCTION
            ),
            Junction(
                source=tmp_path / "c", target=tmp_path / "d", junction_type=JunctionType.SYMLINK
            ),
        ]
    )
    assert window.table_view.isSortingEnabled()
    window.type_filter.setCurrentIndex(2)
    assert window.filter_model.rowCount() == 1
    window.clear_filters()
    assert window.filter_model.rowCount() == 2


def test_failed_progress_dialog_can_close(qtbot):
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    dialog = ProgressDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.set_operation_finished(False, "failure")
    assert dialog.close()


def test_preview_shows_disk_free_bytes(qtbot, monkeypatch, tmp_path):
    from winlink.ui.dialogs.preview_dialog import PreviewDialog
    from winlink.core import process_manager

    target = tmp_path / "target"
    target.mkdir()
    (target / "data").write_bytes(b"abc")
    monkeypatch.setattr(file_ops, "get_available_disk_space", lambda path: 2048)
    monkeypatch.setattr(process_manager, "get_processes_using_directory", lambda path: [])
    dialog = PreviewDialog(target, tmp_path / "new" / "nested")
    qtbot.addWidget(dialog)
    assert "Espaço disponível: 2.0 KB" in dialog.preview_text.toPlainText()
    assert dialog.confirm_btn.isEnabled()


def test_scan_worker_passes_app_owned_paths(monkeypatch, tmp_path):
    from winlink.core import scanner
    from winlink.core.models import ScanResult

    scan = Mock(return_value=ScanResult())
    monkeypatch.setattr(scanner, "scan_directories", scan)
    known = {tmp_path / "link"}
    worker = main_window.ScanWorker([tmp_path], known)
    worker.run()
    scan.assert_called_once_with([tmp_path], recursive=True, known_junctions=known)


@pytest.mark.parametrize("keep_source", [True, False])
def test_undo_move_back_respects_backup(qtbot, monkeypatch, tmp_path, keep_source):
    from winlink.core.models import Junction, JunctionType, UndoStrategy

    source, target = tmp_path / "storage", tmp_path / "link"
    source.mkdir()
    (source / "data").write_text("content")
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy.MOVE_BACK
    dialog.get_keep_source.return_value = keep_source
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    monkeypatch.setattr(operations, "remove_junction", lambda path: True)
    window = Mock()
    main_window.MainWindow.undo_junction(window, junction)
    assert (target / "data").read_text() == "content"
    assert source.exists() == keep_source
    assert window.history_manager.add_operation.call_args.kwargs["success"] is True


def test_undo_missing_source_does_not_remove_link(qtbot, monkeypatch, tmp_path):
    from winlink.core.models import Junction, JunctionType, UndoStrategy

    junction = Junction(
        source=tmp_path / "missing", target=tmp_path / "link", junction_type=JunctionType.JUNCTION
    )
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy.MOVE_BACK
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    remove = Mock()
    monkeypatch.setattr(operations, "remove_junction", remove)
    window = Mock()
    main_window.MainWindow.undo_junction(window, junction)
    remove.assert_not_called()
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False


def test_properties_counts_files_and_folders(qtbot, tmp_path):
    from winlink.core.models import Junction, JunctionType
    from winlink.ui.dialogs.properties_dialog import PropertiesDialog

    (tmp_path / "folder").mkdir()
    (tmp_path / "a").write_text("a")
    (tmp_path / "folder" / "b").write_text("b")
    dialog = PropertiesDialog(
        Junction(
            source=tmp_path,
            target=tmp_path / "link",
            junction_type=JunctionType.JUNCTION,
            size_bytes=0,
        )
    )
    qtbot.addWidget(dialog)
    assert dialog.file_count_label.text() == "2"
    assert dialog.folder_count_label.text() == "1"
    assert dialog.size_label.text() == "0.0 B"


def test_create_dialog_rejects_relative_and_identical_inputs(qtbot, tmp_path):
    from winlink.ui.dialogs.create_junction_dialog import CreateJunctionDialog

    dialog = CreateJunctionDialog()
    qtbot.addWidget(dialog)
    dialog.source_edit.setText(str(tmp_path))
    dialog.target_edit.setText("relative")
    assert not dialog.create_btn.isEnabled()
    dialog.target_edit.setText(str(tmp_path))
    assert not dialog.create_btn.isEnabled()
    dialog.target_edit.setText(str(tmp_path / "other"))
    assert dialog.create_btn.isEnabled()


def test_settings_dialog_saves_and_reloads(qtbot, monkeypatch, tmp_path):
    from winlink.core.config import AppSettings, get_settings
    from winlink.ui.dialogs.settings_dialog import SettingsDialog

    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings = AppSettings(scan_directories=[str(tmp_path)])
    dialog = SettingsDialog(settings)
    qtbot.addWidget(dialog)
    dialog.theme_combo.setCurrentText("dark")
    dialog.warn_nested_checkbox.setChecked(False)
    dialog.save_settings()
    loaded = get_settings()
    assert loaded.theme_mode == "dark"
    assert loaded.warn_nested_junctions is False
    assert dialog.result() == main_window.QDialog.DialogCode.Accepted


def test_history_dialog_filters_and_clears(qtbot, tmp_path):
    from winlink.core.history import HistoryManager
    from winlink.core.models import OperationType
    from winlink.ui.dialogs.history_dialog import HistoryDialog

    manager = HistoryManager(tmp_path / "history.json")
    manager.add_operation(OperationType.CREATE_JUNCTION)
    manager.add_operation(OperationType.UNDO_OPERATION)
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    assert dialog.table_model.rowCount() == 2
    dialog.type_combo.setCurrentText(OperationType.CREATE_JUNCTION.value)
    assert dialog.table_model.rowCount() == 1
    dialog.clear_filters()
    assert dialog.table_model.rowCount() == 2


def test_undo_dialog_strategy_selection(qtbot, tmp_path):
    from winlink.core.models import UndoStrategy
    from winlink.ui.dialogs.undo_dialog import UndoDialog

    dialog = UndoDialog(tmp_path / "source", tmp_path / "target")
    qtbot.addWidget(dialog)
    dialog.duplicate_radio.click()
    assert dialog.get_strategy() == UndoStrategy.DUPLICATE
    dialog.keep_source_checkbox.setChecked(True)
    dialog.remove_only_radio.click()
    dialog.accept()
    assert dialog.get_strategy() == UndoStrategy.REMOVE_ONLY
    assert not dialog.get_keep_source()


def test_progress_cancellation_emits_once_and_waits_for_completion(qtbot):
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    dialog = ProgressDialog()
    qtbot.addWidget(dialog)
    requests = []
    dialog.cancellation_requested.connect(lambda: requests.append(True))
    dialog.show()
    dialog.cancel_operation()
    dialog.cancel_operation()
    assert requests == [True]
    assert dialog.was_cancelled()
    assert dialog.isVisible()
    dialog.set_operation_finished(False, "Cancelado")
    assert dialog.cancel_btn.isEnabled()
    assert dialog.close()


def test_preview_blocks_overlapping_paths(qtbot, tmp_path):
    from winlink.ui.dialogs.preview_dialog import PreviewDialog

    dialog = PreviewDialog(tmp_path / "child", tmp_path)
    qtbot.addWidget(dialog)
    assert not dialog.confirm_btn.isEnabled()
    assert "non-overlapping" in dialog.preview_text.toPlainText()


@pytest.mark.parametrize("creation_succeeds", [True, False])
def test_window_creation_real_copy_and_rollback(qtbot, monkeypatch, tmp_path, creation_succeeds):
    import os
    from winlink.core.models import ValidationResult

    source, target = tmp_path / "storage", tmp_path / "original"
    target.mkdir()
    (target / "payload").write_text("preserved")
    monkeypatch.setattr(
        validators, "validate_junction_creation", lambda *args: ValidationResult(is_valid=True)
    )
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    if not creation_succeeds:
        monkeypatch.setattr(operations, "create_junction", lambda *args: False)
    window = Mock()
    # Real progress widget requires a QWidget parent, so use a factory without the mock parent.
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    dialogs = []

    def progress(title, parent):
        dialog = ProgressDialog(title)
        qtbot.addWidget(dialog)
        dialogs.append(dialog)
        return dialog

    monkeypatch.setattr(main_window, "ProgressDialog", progress)
    main_window.MainWindow.create_junction(window, target, source)
    assert (target / "payload").read_text() == "preserved"
    assert (source / "payload").read_text() == "preserved"
    assert target.is_junction() == creation_succeeds
    assert not list(tmp_path.glob("*.winlink-backup-*"))
    assert window.history_manager.add_operation.call_args.kwargs["success"] == creation_succeeds
    if creation_succeeds:
        assert operations.remove_junction(target)
    assert os.path.exists(source / "payload")


def test_window_cannot_close_during_file_operation():
    window = Mock()
    window._operation_active = True
    window.scan_worker = None
    event = Mock()
    main_window.MainWindow.closeEvent(window, event)
    event.ignore.assert_called_once()
    event.accept.assert_not_called()


def test_window_can_close_when_idle():
    window = Mock()
    window._operation_active = False
    window.scan_worker = None
    window.settings.remember_window_size = False
    event = Mock()
    main_window.MainWindow.closeEvent(window, event)
    event.accept.assert_called_once()
    event.ignore.assert_not_called()


def test_undo_failed_copy_preserves_real_junction(qtbot, monkeypatch, tmp_path):
    from winlink.core.models import Junction, JunctionType, UndoStrategy

    source, target = tmp_path / "source", tmp_path / "link"
    source.mkdir()
    (source / "data").write_text("keep")
    assert operations.create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy.MOVE_BACK
    dialog.get_keep_source.return_value = False
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    monkeypatch.setattr(file_ops, "copy_directory_with_metadata", lambda *args, **kwargs: False)
    window = Mock()
    main_window.MainWindow.undo_junction(window, junction)
    assert target.is_junction()
    assert (target / "data").read_text() == "keep"
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False
    assert operations.remove_junction(target)


def test_settings_save_failure_preserves_active_preferences(qtbot, monkeypatch, tmp_path):
    from winlink.core.config import AppSettings
    from winlink.ui.dialogs import settings_dialog

    settings = AppSettings(theme_mode="light", scan_directories=[str(tmp_path)])
    dialog = settings_dialog.SettingsDialog(settings)
    qtbot.addWidget(dialog)
    dialog.theme_combo.setCurrentText("dark")

    def fail(candidate):
        raise PermissionError("locked")

    monkeypatch.setattr(settings_dialog, "save_settings", fail)
    monkeypatch.setattr(settings_dialog.QMessageBox, "critical", Mock())
    dialog.save_settings()
    assert settings.theme_mode == "light"
    assert dialog.result() != main_window.QDialog.DialogCode.Accepted


def test_history_export_writes_valid_json(qtbot, monkeypatch, tmp_path):
    import json
    from winlink.core.history import HistoryManager
    from winlink.core.models import OperationType
    from winlink.ui.dialogs import history_dialog

    manager = HistoryManager(tmp_path / "history.json")
    manager.add_operation(
        OperationType.CREATE_JUNCTION, source=tmp_path / "origem", target=tmp_path / "destino"
    )
    dialog = history_dialog.HistoryDialog(manager)
    qtbot.addWidget(dialog)
    exported = tmp_path / "export.json"
    monkeypatch.setattr(
        history_dialog.QFileDialog, "getSaveFileName", lambda *a: (str(exported), "")
    )
    monkeypatch.setattr(history_dialog.QMessageBox, "information", Mock())
    dialog.export_history()
    data = json.loads(exported.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["operation_type"] == "CREATE_JUNCTION"
    assert data[0]["source"] == str(tmp_path / "origem")


def test_history_failed_clear_does_not_report_success(qtbot, monkeypatch):
    from winlink.ui.dialogs import history_dialog

    manager = Mock()
    manager.get_history.return_value = []
    manager.clear_history.return_value = False
    dialog = history_dialog.HistoryDialog(manager)
    qtbot.addWidget(dialog)
    monkeypatch.setattr(
        history_dialog.QMessageBox,
        "question",
        lambda *a: history_dialog.QMessageBox.StandardButton.Yes,
    )
    error, success = Mock(), Mock()
    monkeypatch.setattr(history_dialog.QMessageBox, "critical", error)
    monkeypatch.setattr(history_dialog.QMessageBox, "information", success)
    dialog.clear_history()
    error.assert_called_once()
    success.assert_not_called()


def test_history_date_filters_exclude_old_records(qtbot, tmp_path):
    from datetime import datetime, timedelta
    from winlink.core.models import OperationRecord, OperationType
    from winlink.ui.dialogs.history_dialog import HistoryDialog

    now = datetime.now()
    manager = Mock()
    manager.get_history.return_value = [
        OperationRecord(operation_type=OperationType.CREATE_JUNCTION, timestamp=now),
        OperationRecord(
            operation_type=OperationType.UNDO_OPERATION, timestamp=now - timedelta(days=90)
        ),
    ]
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    for label in ["Hoje", "Última semana", "Último mês"]:
        dialog.date_combo.setCurrentText(label)
        assert dialog.table_model.rowCount() == 1
        assert dialog.table_model.get_operation(dialog.table_model.index(0, 0)).timestamp == now
    dialog.clear_filters()
    assert dialog.table_model.rowCount() == 2


def test_proxy_combines_filters_and_sorts_sizes(qtbot, tmp_path):
    from PyQt6.QtCore import Qt
    from winlink.core.models import Creator, Junction, JunctionStatus, JunctionType
    from winlink.ui.junction_filter import JunctionFilterProxyModel
    from winlink.ui.junction_model import JunctionTableModel

    model = JunctionTableModel()
    proxy = JunctionFilterProxyModel()
    proxy.setSourceModel(model)
    model.set_junctions(
        [
            Junction(
                source=tmp_path / "alpha",
                target=tmp_path / "a",
                junction_type=JunctionType.JUNCTION,
                creator=Creator.APP,
                size_bytes=2048,
            ),
            Junction(
                source=tmp_path / "beta",
                target=tmp_path / "b",
                junction_type=JunctionType.SYMLINK,
                creator=Creator.EXISTING,
                size_bytes=10,
            ),
            Junction(
                source=tmp_path / "gamma",
                target=tmp_path / "c",
                junction_type=JunctionType.JUNCTION,
                creator=Creator.APP,
                status=JunctionStatus.BROKEN,
                size_bytes=100,
            ),
        ]
    )
    proxy.sort(4, Qt.SortOrder.AscendingOrder)
    sizes = [
        model.get_junction(proxy.mapToSource(proxy.index(row, 0))).size_bytes for row in range(3)
    ]
    assert sizes == [10, 100, 2048]
    proxy.set_filter_creator(Creator.APP)
    proxy.set_filter_type(JunctionType.JUNCTION)
    proxy.set_filter_status(JunctionStatus.ACTIVE)
    proxy.set_search_text("ALPHA")
    assert proxy.rowCount() == 1
    proxy.set_search_text("beta")
    assert proxy.rowCount() == 0
    proxy.clear_filters()
    assert proxy.rowCount() == 3


def test_active_operation_prevents_reentry():
    window = Mock()
    window._operation_active = True
    main_window.MainWindow.create_junction(window, None, None)
    main_window.MainWindow.undo_junction(window, None)
    main_window.MainWindow.start_scan(window)
    window.history_manager.add_operation.assert_not_called()
    window.status_bar.showMessage.assert_not_called()


@pytest.mark.parametrize(
    "strategy_name,keep_source",
    [("REMOVE_ONLY", False), ("MOVE_BACK", False), ("MOVE_BACK", True), ("DUPLICATE", False)],
)
def test_real_undo_strategies(qtbot, monkeypatch, tmp_path, strategy_name, keep_source):
    from winlink.core.models import Junction, JunctionType, UndoStrategy

    source, target = tmp_path / "storage", tmp_path / "link"
    source.mkdir()
    (source / "data").write_text("payload")
    assert operations.create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy(strategy_name)
    dialog.get_keep_source.return_value = keep_source
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    window = Mock()
    main_window.MainWindow.undo_junction(window, junction)
    assert not target.is_junction()
    assert target.is_dir()
    if strategy_name == "REMOVE_ONLY":
        assert list(target.iterdir()) == []
    else:
        assert (target / "data").read_text() == "payload"
    assert source.exists() == (strategy_name != "MOVE_BACK" or keep_source)
    assert window.history_manager.add_operation.call_args.kwargs["success"] is True
    assert not list(tmp_path.glob("*.winlink-restore-*"))


def test_scan_thread_finds_real_app_junction(qtbot, tmp_path):
    from winlink.core.models import Creator

    storage, root = tmp_path / "storage", tmp_path / "scan"
    storage.mkdir()
    root.mkdir()
    link = root / "link"
    assert operations.create_junction(storage, link)
    worker = main_window.ScanWorker([root], {link})
    try:
        with qtbot.waitSignal(worker.result_ready, timeout=5000) as signal:
            worker.start()
        worker.wait()
        result = signal.args[0]
        assert len(result.junctions) == 1
        assert result.junctions[0].creator == Creator.APP
        assert result.junctions[0].source.resolve() == storage.resolve()
    finally:
        worker.wait()
        assert operations.remove_junction(link)


def test_properties_shows_only_related_history(qtbot, tmp_path):
    from winlink.core.history import HistoryManager
    from winlink.core.models import Junction, JunctionType, OperationType
    from winlink.ui.dialogs.properties_dialog import PropertiesDialog

    manager = HistoryManager(tmp_path / "history.json")
    target = tmp_path / "link"
    manager.add_operation(OperationType.CREATE_JUNCTION, target=target)
    manager.add_operation(OperationType.UNDO_OPERATION, target=tmp_path / "other")
    dialog = PropertiesDialog(
        Junction(source=tmp_path, target=target, junction_type=JunctionType.JUNCTION),
        history_manager=manager,
    )
    qtbot.addWidget(dialog)
    assert "CREATE_JUNCTION" in dialog.history_label.text()
    assert "UNDO_OPERATION" not in dialog.history_label.text()


def test_close_persists_window_size(monkeypatch, tmp_path):
    from winlink.core.config import AppSettings, get_settings

    monkeypatch.setenv("APPDATA", str(tmp_path))
    window = Mock()
    window._operation_active = False
    window.scan_worker = None
    window.settings = AppSettings()
    window.width.return_value = 980
    window.height.return_value = 720
    event = Mock()
    main_window.MainWindow.closeEvent(window, event)
    assert get_settings().window_width == 980
    assert get_settings().window_height == 720


def test_undo_commit_failure_recreates_original_junction(qtbot, monkeypatch, tmp_path):
    from pathlib import Path
    from winlink.core.models import Junction, JunctionType, UndoStrategy

    source, target = tmp_path / "storage", tmp_path / "link"
    source.mkdir()
    (source / "payload").write_text("keep")
    assert operations.create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy.DUPLICATE
    dialog.get_keep_source.return_value = False
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    rename = Path.rename

    def fail_commit(path, destination):
        if ".winlink-restore-" in path.name:
            raise PermissionError("commit denied")
        return rename(path, destination)

    monkeypatch.setattr(Path, "rename", fail_commit)
    window = Mock()
    main_window.MainWindow.undo_junction(window, junction)
    assert target.is_junction()
    assert (target / "payload").read_text() == "keep"
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False
    assert operations.remove_junction(target)


def test_undo_insufficient_space_keeps_original_link(qtbot, monkeypatch, tmp_path):
    from winlink.core.models import Junction, JunctionType, UndoStrategy, ValidationResult

    source, target = tmp_path / "storage", tmp_path / "link"
    source.mkdir()
    assert operations.create_junction(source, target)
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy.DUPLICATE
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    monkeypatch.setattr(
        validators,
        "validate_disk_space",
        lambda *a: ValidationResult(is_valid=False, errors=["insufficient space"]),
    )
    window = Mock()
    main_window.MainWindow.undo_junction(
        window, Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    )
    assert target.is_junction()
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False
    assert operations.remove_junction(target)


def test_refresh_during_scan_is_queued(qtbot, monkeypatch, tmp_path):
    from threading import Event
    from winlink.core import scanner
    from winlink.core.config import AppSettings
    from winlink.core.models import ScanResult

    released = Event()
    calls = []

    def scan(*args, **kwargs):
        calls.append(True)
        if len(calls) == 1:
            assert released.wait(3)
        return ScanResult()

    monkeypatch.setattr(scanner, "scan_directories", scan)
    monkeypatch.setattr(
        main_window, "get_settings", lambda: AppSettings(scan_directories=[str(tmp_path)])
    )
    window = main_window.MainWindow()
    qtbot.addWidget(window)
    first = window.scan_worker
    window.start_scan()
    assert window.scan_worker is first
    assert window._scan_pending
    released.set()
    qtbot.waitUntil(lambda: len(calls) == 2 and not window.scan_worker.isRunning(), timeout=5000)
    assert not window._scan_pending


def test_successful_creation_warns_when_history_save_fails(qtbot, monkeypatch, tmp_path):
    from winlink.core.models import ValidationResult

    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    monkeypatch.setattr(
        validators, "validate_junction_creation", lambda *a: ValidationResult(is_valid=True)
    )
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    messages = Mock()
    monkeypatch.setattr(main_window, "QMessageBox", messages)
    window = Mock()
    window.history_manager.add_operation.return_value = False
    main_window.MainWindow.create_junction(window, target, source)
    assert target.is_junction()
    messages.warning.assert_called_once()
    assert operations.remove_junction(target)


def test_undo_refuses_link_changed_since_scan(qtbot, monkeypatch, tmp_path):
    from winlink.core.models import Junction, JunctionType, UndoStrategy

    old, current, target = tmp_path / "old", tmp_path / "current", tmp_path / "link"
    old.mkdir()
    current.mkdir()
    (old / "data").write_text("old data")
    (current / "data").write_text("current data")
    assert operations.create_junction(current, target)
    dialog = Mock()
    dialog.exec.return_value = main_window.QDialog.DialogCode.Accepted
    dialog.get_strategy.return_value = UndoStrategy.MOVE_BACK
    dialog.get_keep_source.return_value = False
    monkeypatch.setattr(main_window, "UndoDialog", Mock(return_value=dialog))
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    window = Mock()
    main_window.MainWindow.undo_junction(
        window, Junction(source=old, target=target, junction_type=JunctionType.JUNCTION)
    )
    assert target.resolve() == current.resolve()
    assert (old / "data").read_text() == "old data"
    assert (current / "data").read_text() == "current data"
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False
    assert operations.remove_junction(target)


def test_backup_cleanup_failure_keeps_success_and_records_backup(qtbot, monkeypatch, tmp_path):
    from winlink.core.models import ValidationResult

    source, target = tmp_path / "source", tmp_path / "target"
    target.mkdir()
    (target / "payload").write_text("keep")
    monkeypatch.setattr(
        validators, "validate_junction_creation", lambda *a: ValidationResult(is_valid=True)
    )
    monkeypatch.setattr(main_window, "ProgressDialog", Mock())
    messages = Mock()
    monkeypatch.setattr(main_window, "QMessageBox", messages)
    monkeypatch.setattr(file_ops, "delete_directory", lambda path: False)
    window = Mock()
    main_window.MainWindow.create_junction(window, target, source)
    assert target.is_junction()
    record = window.history_manager.add_operation.call_args.kwargs
    assert record["success"] is True
    backups = record["metadata"]["preserved_backups"]
    assert len(backups) == 1
    from pathlib import Path

    assert (Path(backups[0]) / "payload").read_text() == "keep"
    messages.warning.assert_called_once()
    assert operations.remove_junction(target)


def test_preview_computation_keeps_ui_responsive(qtbot, monkeypatch, tmp_path):
    from threading import Event
    from PyQt6.QtCore import QTimer
    from winlink.ui.dialogs import preview_dialog

    released = Event()

    def build(target, source):
        assert released.wait(2)
        return "computed", True

    monkeypatch.setattr(preview_dialog, "build_preview", build)
    QTimer.singleShot(20, released.set)
    dialog = preview_dialog.PreviewDialog(tmp_path / "target", tmp_path / "source")
    qtbot.addWidget(dialog)
    assert dialog.preview_text.toPlainText() == "computed"
    assert dialog.confirm_btn.isEnabled()


def test_creation_cancelled_during_copy_preserves_original(qtbot, monkeypatch, tmp_path):
    from threading import Event
    from PyQt6.QtCore import QTimer
    from winlink.core.models import ValidationResult
    from winlink.ui.dialogs.progress_dialog import ProgressDialog
    source, target = tmp_path / "storage", tmp_path / "original"
    target.mkdir()
    (target / "a").write_text("first")
    (target / "b").write_text("second")
    monkeypatch.setattr(validators, "validate_junction_creation", lambda *a: ValidationResult(is_valid=True))
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    dialogs = []
    released = Event()
    original_copy = file_ops.shutil.copy2
    def copy(src, dst):
        assert released.wait(2)
        return original_copy(src, dst)
    monkeypatch.setattr(file_ops.shutil, "copy2", copy)
    def progress(title, parent):
        dialog = ProgressDialog(title)
        qtbot.addWidget(dialog)
        dialogs.append(dialog)
        return dialog
    monkeypatch.setattr(main_window, "ProgressDialog", progress)
    def cancel():
        dialogs[0].cancel_operation()
        released.set()
    QTimer.singleShot(30, cancel)
    window = Mock()
    main_window.MainWindow.create_junction(window, target, source)
    assert not target.is_junction()
    assert (target / "a").read_text() == "first"
    assert (target / "b").read_text() == "second"
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False
    assert not list(tmp_path.glob("*.winlink-backup-*"))

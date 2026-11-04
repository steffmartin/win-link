"""End-to-end phase 5 regression coverage using isolated filesystem data."""

import time
from threading import Event
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox

from winlink.core.cache import CacheManager
from winlink.core.models import Creator, Junction, JunctionType, OperationType, ScanResult
from winlink.core.operations import create_hard_link
from winlink.core.scanner import scan_directories, scan_directory
from winlink.core.validators import validate_junction_creation
from winlink.ui import main_window


def test_cache_does_not_cross_scan_directories(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    original = first / "original.txt"
    original.write_text("keep")
    assert create_hard_link(original, first / "link.txt")
    assert scan_directories([first], use_cache=True).junctions
    assert not scan_directories([second], use_cache=True).junctions


def test_empty_cache_is_usable_and_fresh_scan_bypasses_it(tmp_path, monkeypatch):
    from winlink.core import scanner

    CacheManager().save(ScanResult(scanned_directories=[tmp_path]))
    scan = Mock(return_value=[])
    monkeypatch.setattr(scanner, "scan_directory", scan)
    scanner.scan_directories([tmp_path], use_cache=True)
    scan.assert_not_called()
    scanner.scan_directories([tmp_path], use_cache=False)
    scan.assert_called_once()


def test_hardlink_discovery_has_another_name_as_source(tmp_path):
    source, link = tmp_path / "açúcar.txt", tmp_path / "referência.txt"
    source.write_text("keep")
    assert create_hard_link(source, link)
    junctions = scan_directory(tmp_path)
    assert len(junctions) == 2
    assert all(j.source != j.target and j.source.samefile(j.target) for j in junctions)


@pytest.mark.parametrize("link_type", [JunctionType.HARDLINK, JunctionType.SYMLINK])
def test_file_link_rejects_existing_target(tmp_path, link_type):
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_text("original")
    target.write_text("preserve")
    assert not validate_junction_creation(source, target, link_type).is_valid
    assert target.read_text() == "preserve"


@pytest.mark.parametrize("link_type", [JunctionType.HARDLINK, JunctionType.SYMLINK])
def test_ui_file_creation_and_removal(qtbot, monkeypatch, tmp_path, link_type):
    source, target = tmp_path / "arquivo original.txt", tmp_path / "novo link.txt"
    source.write_text("preserve")
    messages = Mock()
    messages.StandardButton = QMessageBox.StandardButton
    monkeypatch.setattr(main_window, "QMessageBox", messages)
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    def progress(title, parent):
        dialog = ProgressDialog(title)
        qtbot.addWidget(dialog)
        return dialog

    monkeypatch.setattr(main_window, "ProgressDialog", progress)
    window = Mock()
    main_window.MainWindow.create_link(window, target, source, link_type)
    if link_type == JunctionType.SYMLINK and not target.exists():
        # A standard Windows account without Developer Mode must fail safely.
        assert source.read_text() == "preserve"
        assert window.history_manager.add_operation.call_args.kwargs["success"] is False
        messages.critical.assert_called_once()
        return
    assert target.samefile(source)
    junction = Junction(
        source=source,
        target=target,
        junction_type=link_type,
        is_directory=False,
        creator=Creator.APP,
    )
    main_window.QMessageBox.question.return_value = main_window.QMessageBox.StandardButton.Yes
    main_window.MainWindow.remove_file_link(window, junction)
    assert not target.exists()
    assert source.read_text() == "preserve"


def test_history_undo_emits_verified_link(qtbot, tmp_path):
    from winlink.core.history import HistoryManager
    from winlink.ui.dialogs.history_dialog import HistoryDialog

    source, target = tmp_path / "original", tmp_path / "alias"
    source.write_text("original")
    assert create_hard_link(source, target)
    manager = HistoryManager(tmp_path / "history.json")
    manager.add_operation(OperationType.CREATE_HARDLINK, source, target)
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    dialog.table_view.setCurrentIndex(dialog.table_model.index(0, 0))
    with qtbot.waitSignal(dialog.undo_requested) as signal:
        dialog.undo_selected()
    assert signal.args[0].target == target


def test_large_file_cancel_leaves_no_partial_file(tmp_path):
    from winlink.core.file_ops import copy_directory_with_metadata

    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    with (source / "large.bin").open("wb") as stream:
        stream.truncate(12 * 1024 * 1024)
    checks = 0

    def cancel():
        nonlocal checks
        checks += 1
        if checks == 5:
            raise RuntimeError("cancel")

    assert not copy_directory_with_metadata(source, destination, check_cancelled=cancel)
    assert not list(destination.iterdir())
    assert (source / "large.bin").stat().st_size == 12 * 1024 * 1024


def test_copy_does_not_overwrite_external_collision(tmp_path, monkeypatch):
    from winlink.core import file_ops

    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    (source / "file").write_text("copy")
    copy = file_ops.shutil.copy2

    def race(src, dst):
        result = copy(src, dst)
        (destination / "file").write_text("external change")
        return result

    monkeypatch.setattr(file_ops.shutil, "copy2", race)
    assert not file_ops.copy_directory_with_metadata(source, destination)
    assert (destination / "file").read_text() == "external change"
    assert not list(destination.glob("*.tmp"))


def test_properties_statistics_keep_event_loop_responsive(qtbot, monkeypatch, tmp_path):
    from winlink.ui.dialogs import properties_dialog

    release = Event()

    def counts(path):
        assert release.wait(2)
        return 4, 3

    monkeypatch.setattr(properties_dialog, "count_entries", counts)
    QTimer.singleShot(20, release.set)
    dialog = properties_dialog.PropertiesDialog(
        Junction(source=tmp_path, target=tmp_path / "link", junction_type=JunctionType.JUNCTION)
    )
    qtbot.addWidget(dialog)
    assert dialog.file_count_label.text() == "4"


def test_stress_cache_and_table_10000_entries(qtbot, tmp_path):
    from winlink.ui.junction_model import JunctionTableModel

    junctions = [
        Junction(
            source=tmp_path / str(i),
            target=tmp_path / f"link{i}",
            junction_type=JunctionType.JUNCTION,
        )
        for i in range(10000)
    ]
    manager = CacheManager(tmp_path / "cache.json")
    assert manager.save(ScanResult(junctions=junctions))
    start = time.perf_counter()
    model = JunctionTableModel()
    model.set_junctions(manager.load().to_junctions())
    assert model.rowCount() == 10000
    assert time.perf_counter() - start < 3


def test_creation_preserves_original_when_copy_sees_external_changes(qtbot, monkeypatch, tmp_path):
    from winlink.core import file_ops
    from winlink.core.models import ValidationResult
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    source, target = tmp_path / "storage", tmp_path / "original"
    target.mkdir()
    (target / "payload").write_text("original")
    monkeypatch.setattr(
        "winlink.core.validators.validate_junction_creation",
        lambda *a: ValidationResult(is_valid=True),
    )
    original_copy = file_ops.copy_directory_with_metadata

    def copy(*args, **kwargs):
        result = original_copy(*args, **kwargs)
        (target / "external.txt").write_text("external")
        return result

    monkeypatch.setattr(file_ops, "copy_directory_with_metadata", copy)

    def progress(title, parent):
        dialog = ProgressDialog(title)
        qtbot.addWidget(dialog)
        return dialog

    monkeypatch.setattr(main_window, "ProgressDialog", progress)
    monkeypatch.setattr(main_window, "QMessageBox", Mock())
    window = Mock()
    main_window.MainWindow.create_junction(window, target, source)
    assert not target.is_junction()
    assert (target / "external.txt").read_text() == "external"
    assert (target / "payload").read_text() == "original"
    assert window.history_manager.add_operation.call_args.kwargs["success"] is False


def test_cache_rejects_unknown_version(tmp_path):
    manager = CacheManager(tmp_path / "cache.json")
    manager.cache_path.write_text('{"version":"999"}')
    assert manager.load() is None


def test_long_unicode_paths_preserve_files(tmp_path):
    from winlink.core.file_ops import copy_directory_with_metadata

    source = tmp_path / "origem"
    destination = tmp_path / "cópia"
    nested = source
    for number in range(6):
        nested = nested / ("diretório longo com espaços " + str(number) * 20)
    nested.mkdir(parents=True)
    original = nested / "relatório ação.txt"
    original.write_text("conteúdo preservado", encoding="utf-8")
    assert len(str(original)) > 260
    assert copy_directory_with_metadata(source, destination)
    assert (destination / original.relative_to(source)).read_text(
        encoding="utf-8"
    ) == "conteúdo preservado"

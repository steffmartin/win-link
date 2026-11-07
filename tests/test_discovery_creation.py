from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtWidgets import QMessageBox

from winlink.core.config import AppSettings
from winlink.core.models import Junction, JunctionType
from winlink.ui import main_window


def _window(tmp_path: Path, scan_directories: list[Path]):
    window = Mock()
    window.settings = AppSettings(scan_directories=[str(path) for path in scan_directories])
    window.discovery_exclusions.return_value = ()
    window.tag_manager = Mock()
    window.settings_page = Mock()
    window._data_version = 0
    return window


def _junction(target: Path) -> Junction:
    return Junction(
        source=target.parent / "physical",
        target=target,
        junction_type=JunctionType.JUNCTION,
    )


@pytest.mark.parametrize("excluded", [False, True])
def test_creation_does_not_offer_covered_or_excluded_parent(monkeypatch, tmp_path, excluded):
    root = tmp_path / "included"
    parent = root / "links"
    target = parent / "shortcut"
    window = _window(tmp_path, [root])
    if excluded:
        window.discovery_exclusions.return_value = (parent,)
    messages = Mock()
    monkeypatch.setattr(main_window, "QMessageBox", messages)

    main_window.MainWindow._post_creation_success(window, _junction(target), [])

    messages.question.assert_not_called()
    assert window.tag_manager.set_tags.call_count == 1


def test_creation_offer_can_be_declined_without_changing_discovery(monkeypatch, tmp_path):
    messages = Mock()
    messages.StandardButton = QMessageBox.StandardButton
    messages.question.return_value = QMessageBox.StandardButton.No
    monkeypatch.setattr(main_window, "QMessageBox", messages)
    save = Mock()
    monkeypatch.setattr("winlink.core.config.save_settings", save)
    root = tmp_path / "included"
    parent = tmp_path / "outside" / "links"
    window = _window(tmp_path, [root])

    main_window.MainWindow._post_creation_success(window, _junction(parent / "shortcut"), [])

    assert str(parent.absolute()) in messages.question.call_args.args[2]
    save.assert_not_called()
    assert window.settings.scan_directories == [str(root)]
    assert window._data_version == 0


def test_creation_offer_persists_parent_and_reports_save_failure(monkeypatch, tmp_path):
    messages = Mock()
    messages.StandardButton = QMessageBox.StandardButton
    messages.question.return_value = QMessageBox.StandardButton.Yes
    monkeypatch.setattr(main_window, "QMessageBox", messages)
    root = tmp_path / "included"
    parent = tmp_path / "outside" / "links"
    window = _window(tmp_path, [root])
    save = Mock()
    monkeypatch.setattr("winlink.core.config.save_settings", save)

    main_window.MainWindow._post_creation_success(window, _junction(parent / "shortcut"), [])

    save.assert_called_once()
    assert str(parent.absolute()) in window.settings.scan_directories
    window.settings_page.load_settings.assert_called_once_with(window.settings)
    assert window._data_version == 1

    save.side_effect = OSError("read-only settings")
    failing_window = _window(tmp_path, [root])
    main_window.MainWindow._post_creation_success(
        failing_window, _junction(parent / "another-shortcut"), []
    )
    assert failing_window.settings.scan_directories == [str(root)]
    assert failing_window._data_version == 0
    messages.warning.assert_called_once()

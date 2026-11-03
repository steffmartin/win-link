"""Tests for MainWindow UI integration"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from winlink.ui.main_window import MainWindow
from winlink.core.models import Junction, JunctionType, JunctionStatus, Creator
from winlink.core.config import AppSettings


@pytest.fixture
def app(qtbot):
    """Fixture for QApplication"""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def main_window(app, qtbot):
    """Fixture for MainWindow"""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_main_window_initialization(main_window):
    """Test MainWindow initialization"""
    assert main_window.windowTitle() == "WinLink"
    assert main_window.theme_manager is not None
    assert main_window.junction_model is not None
    assert main_window.filter_model is not None


def test_main_window_has_toolbar(main_window):
    """Test MainWindow has toolbar"""
    toolbar = main_window.findChild(Qt.QWidget, None)
    # MainWindow should have toolbar
    assert main_window.toolBar() is not None


def test_main_window_has_status_bar(main_window):
    """Test MainWindow has status bar"""
    assert main_window.statusBar() is not None


def test_main_window_has_table_view(main_window):
    """Test MainWindow has table view"""
    assert main_window.table_view is not None
    assert main_window.table_view.model() is not None


def test_search_filter(main_window, qtbot):
    """Test search filter functionality"""
    # Add some test junctions
    junctions = [
        Junction(
            source=Path("D:\\Cache\\.vscode"),
            target=Path("C:\\Users\\steff\\.vscode"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
            creator=Creator.APP,
        ),
        Junction(
            source=Path("D:\\Cache\\.cargo"),
            target=Path("C:\\Users\\steff\\.cargo"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
            creator=Creator.APP,
        ),
    ]
    main_window.junction_model.set_junctions(junctions)

    # Test search
    main_window.search_edit.setText("vscode")
    qtbot.wait(100)
    assert main_window.filter_model.rowCount() == 1

    # Clear search
    main_window.search_edit.clear()
    qtbot.wait(100)
    assert main_window.filter_model.rowCount() == 2


def test_status_filter(main_window, qtbot):
    """Test status filter functionality"""
    junctions = [
        Junction(
            source=Path("D:\\Cache\\.vscode"),
            target=Path("C:\\Users\\steff\\.vscode"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
            creator=Creator.APP,
        ),
        Junction(
            source=Path("D:\\Cache\\.cargo"),
            target=Path("C:\\Users\\steff\\.cargo"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.BROKEN,
            creator=Creator.APP,
        ),
    ]
    main_window.junction_model.set_junctions(junctions)

    # Filter by ACTIVE
    main_window.status_filter.setCurrentIndex(1)  # Ativas
    qtbot.wait(100)
    assert main_window.filter_model.rowCount() == 1

    # Clear filter
    main_window.status_filter.setCurrentIndex(0)  # Todos
    qtbot.wait(100)
    assert main_window.filter_model.rowCount() == 2


def test_clear_filters(main_window, qtbot):
    """Test clear filters functionality"""
    junctions = [
        Junction(
            source=Path("D:\\Cache\\.vscode"),
            target=Path("C:\\Users\\steff\\.vscode"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
            creator=Creator.APP,
        ),
    ]
    main_window.junction_model.set_junctions(junctions)

    # Set filters
    main_window.search_edit.setText("vscode")
    main_window.status_filter.setCurrentIndex(1)  # Ativas
    qtbot.wait(100)

    # Clear filters
    main_window.clear_filter_btn.click()
    qtbot.wait(100)

    assert main_window.search_edit.text() == ""
    assert main_window.status_filter.currentIndex() == 0
    assert main_window.creator_filter.currentIndex() == 0


def test_theme_applied(main_window):
    """Test theme is applied on startup"""
    assert main_window.styleSheet() != ""
    assert len(main_window.styleSheet()) > 0


def test_dialog_code_usage(main_window, qtbot):
    """Test that dialog uses QDialog.DialogCode (not self.DialogCode)"""
    """This test prevents the bug where self.DialogCode was used instead of QDialog.DialogCode"""
    # The bug was in on_new_junction, on_settings, and undo_junction
    # They now correctly use QDialog.DialogCode.Accepted
    # This test verifies the methods can be called without AttributeError
    from winlink.ui.dialogs import CreateJunctionDialog

    dialog = CreateJunctionDialog(main_window)
    # Should not raise AttributeError about DialogCode
    result = dialog.exec()
    assert result in [QDialog.DialogCode.Accepted, QDialog.DialogCode.Rejected]


def test_import_correctness():
    """Test that correct functions are imported from file_ops"""
    """This test prevents ImportError bugs like copy_directory vs copy_directory_with_metadata"""
    from winlink.core import file_ops

    # Verify the correct function names exist
    assert hasattr(file_ops, "copy_directory_with_metadata")
    assert hasattr(file_ops, "calculate_directory_size_recursive")
    assert hasattr(file_ops, "move_directory")
    assert hasattr(file_ops, "delete_directory")

    # Verify incorrect names do NOT exist
    assert not hasattr(file_ops, "copy_directory")
    assert not hasattr(file_ops, "calculate_directory_size")


def test_create_junction_signature():
    """Test create_junction has correct signature"""
    """This test prevents the bug where is_directory parameter was passed incorrectly"""
    from winlink.core.operations import create_junction
    import inspect

    sig = inspect.signature(create_junction)
    params = list(sig.parameters.keys())

    # Should have target and link, NOT is_directory
    assert "target" in params
    assert "link" in params
    assert "is_directory" not in params


def test_validate_junction_creation_signature():
    """Test validate_junction_creation has correct signature"""
    """This test prevents the bug where junction_type parameter was missing"""
    from winlink.core.validators import validate_junction_creation
    import inspect

    sig = inspect.signature(validate_junction_creation)
    params = list(sig.parameters.keys())

    # Should have source, target, and junction_type
    assert "source" in params
    assert "target" in params
    assert "junction_type" in params


def test_target_not_empty_validation():
    """Test that target directory can have files (not an error)"""
    """This test prevents the bug where target not empty was treated as error"""
    from winlink.core.validators import validate_junction_creation
    from winlink.core.models import JunctionType
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()
        target.mkdir()
        (target / "file.txt").write_bytes(b"test")

        result = validate_junction_creation(source, target, JunctionType.JUNCTION)
        # Target can have files - they will be copied to source (should be valid)
        assert result.is_valid is True

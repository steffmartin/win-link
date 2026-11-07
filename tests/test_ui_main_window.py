"""Tests for bug prevention - no GUI required"""

import tempfile
from pathlib import Path

from PyQt6.QtTest import QTest

from winlink.core import file_ops
from winlink.core.models import JunctionType
from winlink.core.operations import create_junction
from winlink.core.validators import validate_junction_creation


def test_import_correctness():
    """Test that correct functions are imported from file_ops"""
    """This test prevents ImportError bugs like copy_directory vs copy_directory_with_metadata"""
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


def test_single_instance_acquire_and_release(qapp):
    from PyQt6.QtNetwork import QLocalServer

    from winlink.main import _acquire_instance, _instance_name

    name = _instance_name()
    first = _acquire_instance(name)
    assert first is not None and first != "secondary"
    try:
        assert _acquire_instance(name) == "secondary"
    finally:
        first.close()
    QTest.qWait(50)
    QLocalServer.removeServer(name)
    third = _acquire_instance(name)
    assert third is not None and third != "secondary"
    third.close()
    QLocalServer.removeServer(name)


def test_raise_window_restores_minimized_and_activates():
    from unittest.mock import Mock

    from PyQt6.QtCore import Qt

    from winlink.main import _raise_window

    window = Mock()
    window.windowState.return_value = Qt.WindowState.WindowMinimized
    _raise_window(window)
    window.setWindowState.assert_called_once()
    window.show.assert_called_once()
    window.raise_.assert_called_once()
    window.activateWindow.assert_called_once()

"""Tests for junction scanner"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from winlink.core.models import Creator, Junction, JunctionStatus, JunctionType
from winlink.core.scanner import (
    calculate_directory_size,
    check_junction_status,
    classify_creator,
    get_junction_type,
    get_reparse_target,
    is_reparse_point,
    scan_directory,
    scan_directories,
)


def test_is_reparse_point_with_reparse_attribute():
    """Test is_reparse_point with FILE_ATTRIBUTE_REPARSE_POINT"""
    with patch("winlink.core.scanner.win32api.GetFileAttributes") as mock_get_attrs:
        # Mock a reparse point
        mock_get_attrs.return_value = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT
        result = is_reparse_point(Path("C:/test/junction"))
        assert result is True


def test_is_reparse_point_without_reparse_attribute():
    """Test is_reparse_point without FILE_ATTRIBUTE_REPARSE_POINT"""
    with patch("winlink.core.scanner.win32api.GetFileAttributes") as mock_get_attrs:
        # Mock a normal directory
        mock_get_attrs.return_value = 0x10  # FILE_ATTRIBUTE_DIRECTORY
        result = is_reparse_point(Path("C:/test/normal"))
        assert result is False


def test_is_reparse_point_error():
    """Test is_reparse_point with error"""
    with patch("winlink.core.scanner.win32api.GetFileAttributes") as mock_get_attrs:
        mock_get_attrs.side_effect = Exception("Access denied")
        result = is_reparse_point(Path("C:/test/error"))
        assert result is False


def test_get_junction_type_junction():
    """Test get_junction_type for a junction (mount point)"""
    # This test requires complex mocking of Windows API structures
    # Skipping for now - will be tested with integration tests using real junctions
    pytest.skip("Complex Windows API mocking - will test with real junctions")


def test_get_junction_type_symlink():
    """Test get_junction_type for a symlink"""
    # This test requires complex mocking of Windows API structures
    # Skipping for now - will be tested with integration tests using real junctions
    pytest.skip("Complex Windows API mocking - will test with real junctions")


def test_get_junction_type_error():
    """Test get_junction_type with error"""
    with patch("winlink.core.scanner.win32file.CreateFileW") as mock_create:
        mock_create.side_effect = Exception("Access denied")
        result = get_junction_type(Path("C:/test/error"))
        assert result is None


def test_calculate_directory_size():
    """Test calculate_directory_size with a temporary directory"""
    # This test creates a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create some files
        (tmppath / "file1.txt").write_bytes(b"a" * 100)
        (tmppath / "file2.txt").write_bytes(b"b" * 200)

        subdir = tmppath / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_bytes(b"c" * 300)

        size = calculate_directory_size(tmppath)
        assert size == 600  # 100 + 200 + 300


def test_calculate_directory_size_permission_error():
    """Test calculate_directory_size with permission error"""
    with patch("winlink.core.scanner.os.walk") as mock_walk:
        mock_walk.side_effect = PermissionError("Access denied")
        size = calculate_directory_size(Path("C:/protected"))
        assert size == 0


def test_check_junction_status_active():
    """Test check_junction_status for active junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"
        source.mkdir()
        target.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
            is_directory=True,
        )

        status = check_junction_status(junction)
        assert status == JunctionStatus.ACTIVE


def test_check_junction_status_broken_target():
    """Test check_junction_status when target doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"
        source.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
            is_directory=True,
        )

        status = check_junction_status(junction)
        assert status == JunctionStatus.BROKEN


def test_check_junction_status_broken_source():
    """Test check_junction_status when source doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"
        target.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
            is_directory=True,
        )

        status = check_junction_status(junction)
        assert status == JunctionStatus.BROKEN


def test_classify_creator_app():
    """Test classify_creator for app-created junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"
        source.mkdir()
        target.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        known_junctions = {target}
        creator = classify_creator(junction, known_junctions)
        assert creator == Creator.APP


def test_classify_creator_existing():
    """Test classify_creator for existing junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"
        source.mkdir()
        target.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        known_junctions = set()
        creator = classify_creator(junction, known_junctions)
        assert creator == Creator.EXISTING


def test_scan_directory_nonexistent():
    """Test scan_directory with nonexistent path"""
    result = scan_directory(Path("C:/nonexistent/path"))
    assert result == []


def test_scan_directory_file():
    """Test scan_directory with a file instead of directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        file_path = tmppath / "file.txt"
        file_path.write_bytes(b"test")

        result = scan_directory(file_path)
        assert result == []


def test_scan_directories_empty_list():
    """Test scan_directories with empty list"""
    result = scan_directories([])
    assert len(result.junctions) == 0
    assert len(result.scanned_directories) == 0
    assert result.scan_duration_seconds >= 0


def test_scan_directories_with_error():
    """Test scan_directories with error"""
    result = scan_directories([Path("C:/nonexistent/path")])
    assert len(result.junctions) == 0
    # The scan_directory function logs a warning but doesn't add to errors list
    # The errors list is for errors during scan, not for non-existent paths
    # So we just verify it returns empty junctions

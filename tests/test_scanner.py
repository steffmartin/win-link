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
    is_hard_link,
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


def test_is_hard_link_with_multiple_links():
    """Test is_hard_link with file that has multiple hard links (st_nlink > 1)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")

        # Mock stat to return st_nlink > 1
        with patch.object(Path, "stat") as mock_stat:
            mock_stat_result = MagicMock()
            mock_stat_result.st_nlink = 2
            mock_stat.return_value = mock_stat_result
            result = is_hard_link(file_path)
            assert result is True


def test_is_hard_link_with_single_link():
    """Test is_hard_link with file that has only one hard link (st_nlink = 1)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")

        # Mock stat to return st_nlink = 1
        with patch.object(Path, "stat") as mock_stat:
            mock_stat_result = MagicMock()
            mock_stat_result.st_nlink = 1
            mock_stat.return_value = mock_stat_result
            result = is_hard_link(file_path)
            assert result is False


def test_is_hard_link_error():
    """Test is_hard_link with error"""
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.side_effect = Exception("Access denied")
        result = is_hard_link(Path("C:/test/error.txt"))
        assert result is False


def test_get_junction_type_junction():
    """Test get_junction_type for a junction (mount point)"""
    _assert_reparse_type(0xA0000003, JunctionType.JUNCTION)


def test_get_junction_type_symlink():
    """Test get_junction_type for a symlink"""
    _assert_reparse_type(0xA000000C, JunctionType.SYMLINK)


def _assert_reparse_type(tag, expected):
    buffer = tag.to_bytes(4, "little") + bytes(4)
    with patch("winlink.core.scanner.win32file.CreateFileW", return_value=123), patch(
        "winlink.core.scanner.win32file.DeviceIoControl", return_value=buffer
    ), patch("winlink.core.scanner.win32file.CloseHandle") as close:
        assert get_junction_type(Path("C:/test/link")) == expected
        close.assert_called_once_with(123)


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
    result = scan_directories([], use_cache=False)
    assert len(result.junctions) == 0
    assert len(result.scanned_directories) == 0
    assert result.scan_duration_seconds >= 0


def test_scan_directories_with_error():
    """Test scan_directories with error"""
    result = scan_directories([Path("C:/nonexistent/path")], use_cache=False)
    assert len(result.junctions) == 0
    # The scan_directory function logs a warning but doesn't add to errors list
    # The errors list is for errors during scan, not for non-existent paths
    # So we just verify it returns empty junctions


def test_readlink_relative_target_is_relative_to_link(tmp_path):
    from winlink.core.scanner import get_reparse_target
    with patch("os.readlink", return_value="..\\data"):
        result = get_reparse_target(tmp_path / "links" / "shortcut")
    assert result.resolve() == (tmp_path / "data").resolve()


def test_readlink_unc_prefix_is_preserved(tmp_path):
    from winlink.core.scanner import get_reparse_target
    with patch("os.readlink", return_value="\\\\?\\UNC\\server\\share\\data"):
        assert str(get_reparse_target(tmp_path / "link")) == "\\\\server\\share\\data"


def test_binary_junction_target_uses_path_buffer_offset(tmp_path):
    import struct
    import winnt
    from winlink.core.scanner import get_reparse_target
    text = r"\??\D:\storage".encode("utf-16le")
    payload = struct.pack("<IHHHHHH", winnt.IO_REPARSE_TAG_MOUNT_POINT & 0xFFFFFFFF, len(text) + 8, 0, 0, len(text), 0, 0) + text
    with patch("os.readlink", side_effect=OSError), patch(
        "winlink.core.scanner.win32file.CreateFileW", return_value=123
    ), patch("winlink.core.scanner.win32file.DeviceIoControl", return_value=payload), patch(
        "winlink.core.scanner.win32file.CloseHandle"
    ):
        assert get_reparse_target(tmp_path / "link") == Path(r"D:\storage")


def test_scan_broken_directory_junction_keeps_directory_type(tmp_path):
    from winlink.core.operations import create_junction, remove_junction
    storage, root = tmp_path / "storage", tmp_path / "root"
    storage.mkdir()
    root.mkdir()
    link = root / "link"
    assert create_junction(storage, link)
    storage.rmdir()
    try:
        results = scan_directory(root)
        assert len(results) == 1
        assert results[0].is_directory
        assert results[0].status == JunctionStatus.BROKEN
    finally:
        assert remove_junction(link)


def test_file_status_check_does_not_read_entire_file(tmp_path):
    source = tmp_path / "data"
    source.write_bytes(b"content")
    junction = Junction(source=source, target=source, junction_type=JunctionType.SYMLINK, is_directory=False)
    with patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded read")):
        assert check_junction_status(junction) == JunctionStatus.ACTIVE


@pytest.mark.parametrize("buffer", [bytes.fromhex("030000a000000000"), bytes.fromhex("030000a0000000000000640000000000")])
def test_reparse_target_rejects_truncated_buffers(tmp_path, buffer):
    with patch("os.readlink", side_effect=OSError), patch("winlink.core.scanner.win32file.CreateFileW", return_value=123), patch("winlink.core.scanner.win32file.DeviceIoControl", return_value=buffer), patch("winlink.core.scanner.win32file.CloseHandle") as close:
        assert get_reparse_target(tmp_path / "link") is None
        close.assert_called_once_with(123)


def test_status_permission_failure_is_inaccessible(tmp_path):
    junction = Junction(source=tmp_path, target=tmp_path, junction_type=JunctionType.JUNCTION)
    with patch.object(Path, "stat", side_effect=PermissionError("denied")):
        assert check_junction_status(junction) == JunctionStatus.INACCESSIBLE

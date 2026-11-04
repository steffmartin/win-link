"""Tests for file operations"""

import tempfile
from pathlib import Path

import pytest

from winlink.core.file_ops import (
    calculate_directory_size_recursive,
    calculate_disk_space_required,
    copy_directory_with_metadata,
    copy_file_with_metadata,
    delete_directory,
    delete_file,
    duplicate_directory,
    duplicate_file,
    ensure_directory_exists,
    get_available_disk_space,
    has_sufficient_disk_space,
    is_directory_empty,
    is_file_in_use,
    move_directory,
    move_file,
)


def test_copy_file_with_metadata():
    """Test copying a file with metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source.txt"
        destination = tmppath / "destination.txt"

        source.write_bytes(b"test content")

        result = copy_file_with_metadata(source, destination)
        assert result is True
        assert destination.exists()
        assert destination.read_bytes() == b"test content"


def test_copy_file_without_metadata():
    """Test copying a file without metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source.txt"
        destination = tmppath / "destination.txt"

        source.write_bytes(b"test content")

        result = copy_file_with_metadata(source, destination, preserve_attributes=False)
        assert result is True
        assert destination.exists()


def test_copy_directory_with_metadata():
    """Test copying a directory with metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        destination = tmppath / "destination"

        source.mkdir()
        (source / "file1.txt").write_bytes(b"content1")
        (source / "file2.txt").write_bytes(b"content2")

        result = copy_directory_with_metadata(source, destination)
        assert result is True
        assert destination.exists()
        assert (destination / "file1.txt").exists()
        assert (destination / "file2.txt").exists()


def test_copy_directory_creates_parent():
    """Test that copy creates parent directories"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        destination = tmppath / "parent" / "destination"

        source.mkdir()
        (source / "file.txt").write_bytes(b"content")

        result = copy_directory_with_metadata(source, destination)
        assert result is True
        assert destination.exists()


def test_move_file():
    """Test moving a file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source.txt"
        destination = tmppath / "destination.txt"

        source.write_bytes(b"test content")

        result = move_file(source, destination)
        assert result is True
        assert not source.exists()
        assert destination.exists()
        assert destination.read_bytes() == b"test content"


def test_move_directory():
    """Test moving a directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        destination = tmppath / "destination"

        source.mkdir()
        (source / "file.txt").write_bytes(b"content")

        result = move_directory(source, destination)
        assert result is True
        assert not source.exists()
        assert destination.exists()
        assert (destination / "file.txt").exists()


def test_duplicate_file():
    """Test duplicating a file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source.txt"
        destination = tmppath / "destination.txt"

        source.write_bytes(b"test content")

        result = duplicate_file(source, destination)
        assert result is True
        assert source.exists()  # Source should still exist
        assert destination.exists()
        assert destination.read_bytes() == b"test content"


def test_duplicate_directory():
    """Test duplicating a directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        destination = tmppath / "destination"

        source.mkdir()
        (source / "file.txt").write_bytes(b"content")

        result = duplicate_directory(source, destination)
        assert result is True
        assert source.exists()  # Source should still exist
        assert destination.exists()
        assert (destination / "file.txt").exists()


def test_is_file_in_use_not_in_use():
    """Test checking if file is not in use"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        file_path = tmppath / "file.txt"
        file_path.write_bytes(b"test")

        result = is_file_in_use(file_path)
        assert result is False


def test_is_file_in_use_nonexistent():
    """Test checking if nonexistent file is in use"""
    result = is_file_in_use(Path("C:/nonexistent/file.txt"))
    assert result is False


def test_calculate_directory_size_recursive():
    """Test calculating directory size"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "test_dir"

        directory.mkdir()
        (directory / "file1.txt").write_bytes(b"a" * 100)
        (directory / "file2.txt").write_bytes(b"b" * 200)

        subdir = directory / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_bytes(b"c" * 300)

        size = calculate_directory_size_recursive(directory)
        assert size == 600


def test_calculate_disk_space_required_file():
    """Test calculating disk space for a file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        file_path = tmppath / "file.txt"
        file_path.write_bytes(b"a" * 1000)

        space = calculate_disk_space_required(file_path)
        assert space == 1000


def test_calculate_disk_space_required_directory():
    """Test calculating disk space for a directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "test_dir"

        directory.mkdir()
        (directory / "file.txt").write_bytes(b"a" * 500)

        space = calculate_disk_space_required(directory)
        assert space == 500


def test_get_available_disk_space():
    """Test getting available disk space"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        space = get_available_disk_space(tmppath)
        assert space > 0


def test_has_sufficient_disk_space():
    """Test checking for sufficient disk space"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Should have enough space for 1 byte
        result = has_sufficient_disk_space(tmppath, 1)
        assert result is True


def test_delete_file():
    """Test deleting a file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        file_path = tmppath / "file.txt"
        file_path.write_bytes(b"test")

        result = delete_file(file_path)
        assert result is True
        assert not file_path.exists()


def test_delete_directory():
    """Test deleting a directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "test_dir"

        directory.mkdir()
        (directory / "file.txt").write_bytes(b"test")

        result = delete_directory(directory)
        assert result is True
        assert not directory.exists()


def test_ensure_directory_exists_creates():
    """Test creating a directory that doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "new_dir"

        result = ensure_directory_exists(directory)
        assert result is True
        assert directory.exists()


def test_ensure_directory_exists_already_exists():
    """Test ensuring a directory that already exists"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "existing_dir"
        directory.mkdir()

        result = ensure_directory_exists(directory)
        assert result is True
        assert directory.exists()


def test_is_directory_empty_true():
    """Test checking if directory is empty"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "empty_dir"
        directory.mkdir()

        result = is_directory_empty(directory)
        assert result is True


def test_is_directory_empty_false():
    """Test checking if directory is not empty"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        directory = tmppath / "non_empty_dir"
        directory.mkdir()
        (directory / "file.txt").write_bytes(b"test")

        result = is_directory_empty(directory)
        assert result is False


def test_directory_copy_conflict_preserves_both_versions(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "data").write_text("incoming")
    (destination / "data").write_text("existing")
    assert not copy_directory_with_metadata(source, destination)
    assert (source / "data").read_text() == "incoming"
    assert (destination / "data").read_text() == "existing"


def test_copy_rejects_destination_inside_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "data").write_text("keep")
    assert not copy_directory_with_metadata(source, source / "nested")
    assert not (source / "nested").exists()


def test_directory_copy_checks_cancellation_between_files(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    for number in range(3):
        (source / str(number)).write_text("preserve")
    checks = []
    def check():
        checks.append(True)
        if len(checks) == 3:
            raise RuntimeError("cancelled")
    assert not copy_directory_with_metadata(source, destination, check_cancelled=check)
    assert len(list(source.iterdir())) == 3
    # Cancellation may happen before publishing the first completed copy.
    assert len(list(destination.iterdir())) <= 1
    assert not list(destination.glob("*.tmp"))


def test_copy_preserves_nested_junction_without_following_it(tmp_path):
    from winlink.core.operations import create_junction, remove_junction
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    # A cycle must be preserved as a link rather than recursively copied.
    nested = source / "cycle"
    assert create_junction(source, nested)
    try:
        assert copy_directory_with_metadata(source, destination)
        assert (destination / "cycle").is_junction()
    finally:
        if (destination / "cycle").is_junction():
            assert remove_junction(destination / "cycle")
        assert remove_junction(nested)


def test_size_calculation_does_not_follow_junction_cycle(tmp_path):
    from winlink.core.operations import create_junction, remove_junction
    from winlink.core.scanner import calculate_directory_size
    from winlink.core.file_ops import calculate_directory_size_recursive
    (tmp_path / "payload").write_bytes(b"12345")
    cycle = tmp_path / "cycle"
    assert create_junction(tmp_path, cycle)
    try:
        assert calculate_directory_size(tmp_path) == 5
        assert calculate_directory_size_recursive(tmp_path) == 5
    finally:
        assert remove_junction(cycle)


def test_is_file_in_use_detects_windows_shared_handle(tmp_path):
    import win32file
    path = tmp_path / "locked"
    path.write_text("payload")
    handle = win32file.CreateFile(str(path), win32file.GENERIC_READ, win32file.FILE_SHARE_READ, None, win32file.OPEN_EXISTING, 0, None)
    try:
        assert is_file_in_use(path)
    finally:
        handle.Close()
    assert not is_file_in_use(path)

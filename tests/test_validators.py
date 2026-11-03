"""Tests for validation functions"""

import tempfile
from pathlib import Path

from winlink.core.models import Junction, JunctionType, ValidationResult
from winlink.core.validators import (
    validate_directory_empty,
    validate_disk_space,
    validate_is_junction,
    validate_is_not_junction,
    validate_junction_creation,
    validate_junction_removal,
    validate_path,
    validate_path_exists,
    validate_path_not_exists,
    validate_permissions,
    validate_undo_operation,
)


def test_validate_path_valid():
    """Test validating a valid path"""
    result = validate_path(Path("C:/valid/path"))
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_path_empty():
    """Test validating an empty path"""
    result = validate_path(Path(""))
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_path_invalid_chars():
    """Test validating path with invalid characters"""
    result = validate_path(Path("C:/invalid|path"))
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_path_long():
    """Test validating a very long path"""
    long_path = Path("C:/" + "a" * 300)
    result = validate_path(long_path)
    assert result.is_valid is True  # Should be valid but with warning
    assert len(result.warnings) > 0


def test_validate_path_relative():
    """Test validating a relative path"""
    result = validate_path(Path("relative/path"))
    assert result.is_valid is True  # Relative paths are valid but generate warning
    assert len(result.warnings) > 0


def test_validate_path_exists_true():
    """Test validating path that exists"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        result = validate_path_exists(tmppath)
        assert result.is_valid is True


def test_validate_path_exists_false():
    """Test validating path that doesn't exist"""
    result = validate_path_exists(Path("C:/nonexistent/path"))
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_path_not_exists_true():
    """Test validating path that doesn't exist"""
    result = validate_path_not_exists(Path("C:/nonexistent/path"))
    assert result.is_valid is True


def test_validate_path_not_exists_false():
    """Test validating path that exists when it shouldn't"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        result = validate_path_not_exists(tmppath)
        assert result.is_valid is False
        assert len(result.errors) > 0


def test_validate_permissions_read():
    """Test validating read permissions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        result = validate_permissions(tmppath, write=False)
        assert result.is_valid is True


def test_validate_permissions_write():
    """Test validating write permissions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        result = validate_permissions(tmppath, write=True)
        assert result.is_valid is True


def test_validate_permissions_nonexistent():
    """Test validating permissions for nonexistent path"""
    result = validate_permissions(Path("C:/nonexistent"), write=False)
    assert result.is_valid is False


def test_validate_disk_space_sufficient():
    """Test validating sufficient disk space"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        result = validate_disk_space(tmppath, 1024)
        assert result.is_valid is True


def test_validate_disk_space_insufficient():
    """Test validating insufficient disk space"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Request more space than available (assuming less than 1PB available)
        result = validate_disk_space(tmppath, 10**15)
        assert result.is_valid is False
        assert len(result.errors) > 0


def test_validate_is_junction_true():
    """Test validating that path is a junction (mocked)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass

        # Mock is_reparse_point to return True
        from unittest.mock import patch

        with patch("winlink.core.validators.is_reparse_point") as mock_is_reparse:
            mock_is_reparse.return_value = True

            result = validate_is_junction(tmppath)
            assert result.is_valid is True


def test_validate_is_junction_false():
    """Test validating that path is a junction when it's not"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass

        result = validate_is_junction(tmppath)
        assert result.is_valid is False
        assert len(result.errors) > 0


def test_validate_is_not_junction_true():
    """Test validating that path is not a junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass

        result = validate_is_not_junction(tmppath)
        assert result.is_valid is True


def test_validate_is_not_junction_false():
    """Test validating that path is not a junction when it is (mocked)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass

        from unittest.mock import patch

        with patch("winlink.core.validators.is_reparse_point") as mock_is_reparse:
            mock_is_reparse.return_value = True

            result = validate_is_not_junction(tmppath)
            assert result.is_valid is False
            assert len(result.errors) > 0


def test_validate_directory_empty_true():
    """Test validating that directory is empty"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass

        result = validate_directory_empty(tmppath)
        assert result.is_valid is True


def test_validate_directory_empty_false():
    """Test validating that directory is empty when it's not"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass
        (tmppath / "file.txt").write_bytes(b"test")

        result = validate_directory_empty(tmppath)
        assert result.is_valid is False
        assert len(result.errors) > 0


def test_validate_directory_empty_not_directory():
    """Test validating directory empty when path is not a directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        file_path = tmppath / "file.txt"
        file_path.write_bytes(b"test")

        result = validate_directory_empty(file_path)
        assert result.is_valid is False
        assert len(result.errors) > 0


def test_validate_junction_creation_valid():
    """Test validating junction creation with valid parameters"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()

        result = validate_junction_creation(source, target, JunctionType.JUNCTION)
        assert result.is_valid is True
        assert len(result.warnings) == 0


def test_validate_junction_creation_target_is_junction():
    """Test validating junction creation when target is already a junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()
        target.mkdir()

        from unittest.mock import patch

        with patch("winlink.core.validators.is_reparse_point") as mock_is_reparse:
            mock_is_reparse.return_value = True

            result = validate_junction_creation(source, target, JunctionType.JUNCTION)
            assert result.is_valid is False
            assert len(result.errors) > 0


def test_validate_junction_creation_target_not_empty():
    """Test validating junction creation when target is not empty"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()
        target.mkdir()
        (target / "file.txt").write_bytes(b"test")

        result = validate_junction_creation(source, target, JunctionType.JUNCTION)
        # Target can have files - they will be copied to source (not an error)
        assert result.is_valid is True
        assert len(result.errors) > 0


def test_validate_junction_creation_hardlink_directory():
    """Test validating hard link creation for directory (should fail)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()  # Source is a directory, which is invalid for hard links

        result = validate_junction_creation(source, target, JunctionType.HARDLINK)
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should have error about hard links being for files only
        assert any("Hard links" in error for error in result.errors)


def test_validate_junction_removal_valid():
    """Test validating junction removal"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        source = tmppath / "source"

        target.mkdir()
        source.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        result = validate_junction_removal(junction)
        # Should have warning about checking for processes
        assert len(result.warnings) > 0


def test_validate_junction_removal_nonexistent():
    """Test validating junction removal for nonexistent junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        source = tmppath / "source"

        source.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        result = validate_junction_removal(junction)
        assert result.is_valid is False
        assert len(result.errors) > 0


def test_validate_undo_operation_valid():
    """Test validating undo operation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        source = tmppath / "source"

        target.mkdir()
        source.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        result = validate_undo_operation(junction, "REMOVE_ONLY")
        assert result.is_valid is True


def test_validate_undo_operation_invalid_strategy():
    """Test validating undo operation with invalid strategy"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        source = tmppath / "source"

        target.mkdir()
        source.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        result = validate_undo_operation(junction, "INVALID_STRATEGY")
        assert result.is_valid is False
        assert len(result.errors) > 0

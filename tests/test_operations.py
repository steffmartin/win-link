"""Tests for junction operations"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from winlink.core.models import Junction, JunctionStatus, JunctionType
from winlink.core.operations import (
    create_hard_link,
    create_junction,
    create_symbolic_link,
    recreate_junction,
    remove_junction,
    verify_junction_integrity,
)


def test_create_symbolic_link_directory():
    """Test creating a symbolic link for a directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        link = tmppath / "link"

        target.mkdir()

        with patch("winlink.core.operations.win32file.CreateSymbolicLink") as mock_create:
            mock_create.return_value = True

            result = create_symbolic_link(target, link, is_directory=True)
            assert result is True
            mock_create.assert_called_once()


def test_create_symbolic_link_file():
    """Test creating a symbolic link for a file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target.txt"
        link = tmppath / "link.txt"

        target.write_bytes(b"test")

        with patch("winlink.core.operations.win32file.CreateSymbolicLink") as mock_create:
            mock_create.return_value = True

            result = create_symbolic_link(target, link, is_directory=False)
            assert result is True
            mock_create.assert_called_once()


def test_create_symbolic_link_failure():
    """Test symbolic link creation failure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        link = tmppath / "link"

        target.mkdir()

        with patch("winlink.core.operations.win32file.CreateSymbolicLink") as mock_create:
            mock_create.return_value = False

            result = create_symbolic_link(target, link, is_directory=True)
            assert result is False


def test_create_hard_link():
    """Test creating a hard link"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target.txt"
        link = tmppath / "link.txt"

        target.write_bytes(b"test")

        with patch("winlink.core.operations.win32file.CreateHardLink") as mock_create:
            mock_create.return_value = True

            result = create_hard_link(target, link)
            assert result is True
            mock_create.assert_called_once()


def test_create_hard_link_failure():
    """Test hard link creation failure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target.txt"
        link = tmppath / "link.txt"

        target.write_bytes(b"test")

        with patch("winlink.core.operations.win32file.CreateHardLink") as mock_create:
            mock_create.return_value = False

            result = create_hard_link(target, link)
            assert result is False


def test_create_junction_target_not_exists():
    """Test creating junction when target doesn't exist (should create it)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        link = tmppath / "link"

        # Mock subprocess.run for mklink
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = create_junction(target, link)
            assert result is True


def test_create_junction_link_not_empty():
    """Test creating junction when link directory is not empty (should fail)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        link = tmppath / "link"

        target.mkdir()
        link.mkdir()
        (link / "file.txt").write_bytes(b"test")

        result = create_junction(target, link)
        assert result is False


def test_create_junction_link_is_file():
    """Test creating junction when link is a file (should fail)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        target = tmppath / "target"
        link = tmppath / "link.txt"

        target.mkdir()
        link.write_bytes(b"test")

        # Mock subprocess.run to simulate mklink failure
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Invalid")

            result = create_junction(target, link)
            assert result is False


def test_remove_junction_nonexistent():
    """Test removing junction that doesn't exist"""
    result = remove_junction(Path("C:/nonexistent/junction"))
    assert result is False


def test_remove_junction_not_reparse_point():
    """Test removing directory that is not a reparse point"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        link = tmppath / "normal_dir"
        link.mkdir()

        result = remove_junction(link)
        assert result is False


def test_remove_junction_success():
    """Test successfully removing a junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        link = tmppath / "junction"

        link.mkdir()

        with patch("winlink.core.operations.win32api.GetFileAttributes") as mock_attrs:
            # Mock as reparse point
            mock_attrs.return_value = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT

            result = remove_junction(link)
            assert result is True


def test_verify_junction_integrity_active():
    """Test verifying an active junction"""
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

        with patch("winlink.core.operations.win32api.GetFileAttributes") as mock_attrs:
            # Mock as reparse point
            mock_attrs.return_value = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT

            result = verify_junction_integrity(junction)
            assert result is True
            assert junction.status == JunctionStatus.ACTIVE


def test_verify_junction_integrity_broken_target():
    """Test verifying junction with broken target"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()
        # Don't create target

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        result = verify_junction_integrity(junction)
        assert result is False
        assert junction.status == JunctionStatus.BROKEN


def test_verify_junction_integrity_broken_source():
    """Test verifying junction with broken source"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        # Don't create source
        target.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        result = verify_junction_integrity(junction)
        assert result is False
        assert junction.status == JunctionStatus.BROKEN


def test_recreate_junction():
    """Test recreating a junction"""
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

        with patch("winlink.core.operations.remove_junction") as mock_remove, patch(
            "winlink.core.operations.create_junction"
        ) as mock_create:
            mock_remove.return_value = True
            mock_create.return_value = True

            result = recreate_junction(junction)
            assert result is True
            mock_remove.assert_called_once_with(target)
            mock_create.assert_called_once_with(source, target)


def test_recreate_junction_symlink():
    """Test recreating a symlink"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()
        target.mkdir()

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.SYMLINK,
            is_directory=True,
        )

        with patch("winlink.core.operations.remove_junction") as mock_remove, patch(
            "winlink.core.operations.create_symbolic_link"
        ) as mock_create:
            mock_remove.return_value = True
            mock_create.return_value = True

            result = recreate_junction(junction)
            assert result is True
            mock_remove.assert_called_once_with(target)
            mock_create.assert_called_once_with(source, target, True)


def test_recreate_junction_hardlink():
    """Test recreating a hard link"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source.txt"
        target = tmppath / "target.txt"

        source.write_bytes(b"test")
        target.write_bytes(b"test")

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.HARDLINK,
            is_directory=False,
        )

        with patch("winlink.core.operations.remove_junction") as mock_remove, patch(
            "winlink.core.operations.create_hard_link"
        ) as mock_create:
            mock_remove.return_value = True
            mock_create.return_value = True

            result = recreate_junction(junction)
            assert result is True
            mock_remove.assert_called_once_with(target)
            mock_create.assert_called_once_with(source, target)

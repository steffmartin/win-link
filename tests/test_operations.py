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


def test_create_symbolic_link_privilege_failure_is_actionable(tmp_path):
    import pywintypes

    from winlink.core.operations import SymbolicLinkPrivilegeError

    source = tmp_path / "source"
    source.mkdir()
    privilege_error = pywintypes.error(
        1314, "CreateSymbolicLinkW", "A required privilege is not held by the client"
    )

    with patch(
        "winlink.core.operations.win32file.CreateSymbolicLink", side_effect=privilege_error
    ):
        with pytest.raises(SymbolicLinkPrivilegeError, match="Modo de Desenvolvedor") as raised:
            create_symbolic_link(source, tmp_path / "link")

    assert "não será iniciada automaticamente" in str(raised.value)


def test_create_symbolic_link_privilege_error_return_is_actionable(tmp_path):
    from winlink.core.operations import SymbolicLinkPrivilegeError

    source = tmp_path / "source"
    source.mkdir()
    with patch("winlink.core.operations.win32file.CreateSymbolicLink", return_value=False), patch(
        "winlink.core.operations.win32api.GetLastError", return_value=1314
    ):
        with pytest.raises(SymbolicLinkPrivilegeError, match="Modo de Desenvolvedor"):
            create_symbolic_link(source, tmp_path / "link")


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


def test_create_junction_target_not_exists(tmp_path):
    """Low-level creation rejects missing storage; the UI creates it first."""
    assert not create_junction(tmp_path / "missing", tmp_path / "link")
    assert not (tmp_path / "link").exists()


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
            mock_attrs.return_value = 0x410  # REPARSE_POINT | DIRECTORY

            result = remove_junction(link)
            assert result is True


def test_verify_junction_integrity_active():
    """Test verifying an active junction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        source = tmppath / "source"
        target = tmppath / "target"

        source.mkdir()
        assert create_junction(source, target)

        junction = Junction(
            source=source,
            target=target,
            junction_type=JunctionType.JUNCTION,
        )

        with patch("winlink.core.operations.win32api.GetFileAttributes") as mock_attrs:
            # Mock as reparse point
            mock_attrs.return_value = 0x410  # REPARSE_POINT | DIRECTORY

            result = verify_junction_integrity(junction)
            assert result is True
            assert junction.status == JunctionStatus.ACTIVE

        assert remove_junction(target)


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


def test_recreate_junction_hardlink(tmp_path):
    source, target = tmp_path / "source", tmp_path / "link"
    source.write_text("preserve")
    junction = Junction(source=source, target=target, junction_type=JunctionType.HARDLINK, is_directory=False)
    assert recreate_junction(junction)
    assert source.samefile(target)
    assert recreate_junction(junction)
    target.unlink()
    target.write_text("unrelated data")
    assert not recreate_junction(junction)
    assert target.read_text() == "unrelated data"


def test_remove_broken_directory_link_uses_attributes():
    import win32con
    link = MagicMock(spec=Path)
    link.__fspath__.return_value = "broken-link"
    link.exists.return_value = False
    link.is_dir.return_value = False
    with patch("winlink.core.operations.os.path.lexists", return_value=True), patch(
        "winlink.core.operations.win32api.GetFileAttributes",
        return_value=win32con.FILE_ATTRIBUTE_REPARSE_POINT | win32con.FILE_ATTRIBUTE_DIRECTORY,
    ):
        assert remove_junction(link)
    link.rmdir.assert_called_once()
    link.unlink.assert_not_called()


def test_recreate_stops_when_removal_fails(tmp_path):
    junction = Junction(source=tmp_path / "data", target=tmp_path / "link", junction_type=JunctionType.JUNCTION)
    with patch("winlink.core.operations.os.path.lexists", return_value=True), patch(
        "winlink.core.operations.remove_junction", return_value=False
    ), patch("winlink.core.operations.create_junction") as create:
        assert not recreate_junction(junction)
        create.assert_not_called()


def test_hard_link_real_api_return(tmp_path):
    source = tmp_path / "data.txt"
    link = tmp_path / "hard.txt"
    source.write_text("shared data")
    assert create_hard_link(source, link)
    assert source.samefile(link)
    assert link.read_text() == "shared data"


def test_symbolic_link_none_return_is_success(tmp_path):
    with patch("winlink.core.operations.win32file.CreateSymbolicLink", return_value=None):
        assert create_symbolic_link(tmp_path / "data", tmp_path / "link")


def test_create_junction_never_deletes_existing_file(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    link = tmp_path / "occupied"
    link.write_text("valuable")
    with patch("subprocess.run") as run:
        assert not create_junction(data, link)
        run.assert_not_called()
    assert link.read_text() == "valuable"


def test_real_junction_lifecycle_preserves_data(tmp_path):
    from winlink.core.scanner import get_reparse_target, get_junction_type
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "payload").write_text("keep")
    link = tmp_path / "junction"
    assert create_junction(storage, link)
    assert link.is_junction()
    assert get_junction_type(link) == JunctionType.JUNCTION
    assert get_reparse_target(link).resolve() == storage.resolve()
    assert (link / "payload").read_text() == "keep"
    assert remove_junction(link)
    assert not link.exists()
    assert (storage / "payload").read_text() == "keep"


def test_real_broken_junction_can_be_removed(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    link = tmp_path / "junction"
    assert create_junction(storage, link)
    storage.rmdir()
    assert not link.exists()
    assert link.is_junction()
    assert remove_junction(link)
    assert not link.is_junction()


def test_real_junction_accepts_shell_metacharacters(tmp_path):
    storage = tmp_path / "storage & (data)"
    storage.mkdir()
    link = tmp_path / "link & (example)"
    assert create_junction(storage, link)
    assert link.is_junction()
    assert link.resolve() == storage.resolve()
    assert remove_junction(link)


def test_real_hard_link_integrity_uses_file_identity(tmp_path):
    source, link = tmp_path / "source", tmp_path / "link"
    source.write_text("data")
    assert create_hard_link(source, link)
    junction = Junction(source=source, target=link, junction_type=JunctionType.HARDLINK, is_directory=False)
    assert verify_junction_integrity(junction)
    link.unlink()
    link.write_text("data")
    assert not verify_junction_integrity(junction)
    assert junction.status == JunctionStatus.BROKEN

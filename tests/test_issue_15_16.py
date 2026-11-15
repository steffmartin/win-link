"""Regressions for access classification and hard-link replacement."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import win32api
import win32con
import win32security

from winlink.core.models import Junction, JunctionStatus, JunctionType
from winlink.core.operations import create_hard_link, create_junction, verify_junction_integrity
from winlink.core.scanner import check_junction_status, scan_directory
from winlink.ui.dialogs.preview_dialog import build_preview


def test_integrity_permission_denial_is_not_a_broken_link(tmp_path):
    source, target = tmp_path / "data", tmp_path / "link"
    source.mkdir()
    assert create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    try:
        with patch.object(Path, "samefile", side_effect=PermissionError("denied")):
            assert not verify_junction_integrity(junction)
        assert junction.status == JunctionStatus.INACCESSIBLE
        assert junction.status_detail
    finally:
        target.rmdir()


def test_directory_enumeration_failure_explains_the_restriction(tmp_path):
    source, target = tmp_path / "data", tmp_path / "link"
    source.mkdir()
    assert create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    try:
        with patch("winlink.core.scanner.os.scandir", side_effect=PermissionError("denied")):
            assert check_junction_status(junction) == JunctionStatus.INACCESSIBLE
        assert "listar" in junction.status_detail.lower()
    finally:
        target.rmdir()


def test_real_directory_list_denial_is_explained(tmp_path):
    source, target = tmp_path / "data", tmp_path / "link"
    source.mkdir()
    assert source.resolve().is_relative_to(tmp_path.resolve())
    assert create_junction(source, target)
    descriptor = win32security.GetNamedSecurityInfo(
        str(source), win32security.SE_FILE_OBJECT, win32security.DACL_SECURITY_INFORMATION
    )
    original_acl = descriptor.GetSecurityDescriptorDacl()
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
    sid_text = win32security.ConvertSidToStringSid(sid)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    try:
        icacls = Path(os.environ["SystemRoot"]) / "System32" / "icacls.exe"
        result = subprocess.run(
            [str(icacls), str(source), "/deny", f"*{sid_text}:(RD)"],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0
        source.stat()
        target.stat()
        with pytest.raises(PermissionError):
            with os.scandir(target):
                pass
        assert check_junction_status(junction) == JunctionStatus.INACCESSIBLE
        assert "listar" in junction.status_detail.lower()
    finally:
        win32security.SetNamedSecurityInfo(
            str(source),
            win32security.SE_FILE_OBJECT,
            win32security.DACL_SECURITY_INFORMATION,
            None,
            None,
            original_acl,
            None,
        )
        target.rmdir()


def test_hard_link_replacement_changes_identity_and_scan(tmp_path):
    source, target = tmp_path / "original.docx", tmp_path / "outro.docx"
    source.write_bytes(b"conteudo original")
    assert create_hard_link(source, target)
    before = (source.stat().st_ino, target.stat().st_ino)
    assert source.samefile(target) and before[0] == before[1]
    assert {j.target for j in scan_directory(tmp_path)} == {source, target}
    replacement = tmp_path / "salvo.docx"
    replacement.write_bytes(b"conteudo salvo")
    replacement.replace(source)
    after = (source.stat().st_ino, target.stat().st_ino)
    assert source.exists() and target.exists() and after[0] != after[1]
    assert source.read_bytes() == b"conteudo salvo"
    assert target.read_bytes() == b"conteudo original"
    assert not scan_directory(tmp_path)
    junction = Junction(
        source=source, target=target, junction_type=JunctionType.HARDLINK, is_directory=False
    )
    assert check_junction_status(junction) == JunctionStatus.BROKEN


def test_hard_link_integrity_never_accepts_a_directory(tmp_path):
    junction = Junction(
        source=tmp_path, target=tmp_path, junction_type=JunctionType.HARDLINK, is_directory=False
    )
    assert not verify_junction_integrity(junction)
    assert junction.status == JunctionStatus.BROKEN


def test_hard_link_preview_warns_about_replacement(tmp_path):
    source, target = tmp_path / "original.docx", tmp_path / "outro.docx"
    source.write_bytes(b"data")
    preview, valid = build_preview(target, source, JunctionType.HARDLINK)
    assert valid
    assert "substitu" in preview.lower()
    assert "serão refletidas" not in preview

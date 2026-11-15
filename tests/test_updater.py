"""Update integrity, user choices and helper lifecycle without using the network."""

import hashlib
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import URLError
from urllib.request import Request

import pytest
from PyQt6.QtWidgets import QWidget

from winlink import update_helper
from winlink.core import updater
from winlink.ui.update_controller import UpdateDialog


def release(version="1.2.0"):
    tag = f"v{version}"
    name = f"WinLink-Setup-{version}.exe"
    base = f"https://github.com/steffmartin/win-link/releases/download/{tag}"
    return {
        "tag_name": tag,
        "assets": [
            {"name": name, "browser_download_url": f"{base}/{name}"},
            {"name": "SHA256SUMS.txt", "browser_download_url": f"{base}/SHA256SUMS.txt"},
        ],
    }


class Response(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}


def serve(monkeypatch, mapping):
    monkeypatch.setattr(updater, "_open", lambda url, timeout=10: Response(mapping[url]))


def test_check_newer_release_and_ignore_one_version(monkeypatch):
    data = release()
    serve(monkeypatch, {updater.RELEASE_API: json.dumps(data).encode()})
    info = updater.check_update("1.1.0")
    assert info and info.version == "1.2.0"
    assert info.installer_url and info.checksum_url
    updater.ignore_version(info.version)
    assert updater.check_update("1.1.0") is None
    assert updater.check_update("1.2.0") is None
    newer = release("1.3.0")
    serve(monkeypatch, {updater.RELEASE_API: json.dumps(newer).encode()})
    assert updater.check_update("1.1.0").version == "1.3.0"


@pytest.mark.parametrize("kind", ["host", "path", "duplicate", "prerelease"])
def test_untrusted_release_metadata_cannot_enable_install(monkeypatch, kind):
    data = release()
    if kind == "host":
        data["assets"][0]["browser_download_url"] = "https://example.com/installer.exe"
    elif kind == "path":
        data["assets"][0]["browser_download_url"] += "?redirect=other"
    elif kind == "duplicate":
        data["assets"].append(data["assets"][0])
    else:
        data["prerelease"] = True
    serve(monkeypatch, {updater.RELEASE_API: json.dumps(data).encode()})
    result = updater.check_update("1.1.0")
    if kind == "prerelease":
        assert result is None
    else:
        assert result and result.installer_url is None and result.checksum_url is None


def test_rejects_unsafe_redirect():
    handler = updater._SafeRedirect()
    with pytest.raises(URLError):
        handler.redirect_request(
            Request("https://github.com/a"), None, 302, "", {}, "http://127.0.0.1/x"
        )


def test_download_verifies_exact_checksum_and_cleans_failure(tmp_path, monkeypatch):
    data = release()
    serve(monkeypatch, {updater.RELEASE_API: json.dumps(data).encode()})
    info = updater.check_update("1.1.0")
    payload = b"synthetic installer"
    checksum = hashlib.sha256(payload).hexdigest()
    directory = tmp_path / "download"
    monkeypatch.setattr(
        updater.tempfile, "mkdtemp", lambda **kwargs: str(directory.mkdir() or directory)
    )
    serve(
        monkeypatch,
        {
            info.checksum_url: f"{checksum}  {info.installer_name}\n".encode(),
            info.installer_url: payload,
        },
    )
    progress = []
    downloaded = updater.download_update(info, lambda *args: progress.append(args))
    assert downloaded.read_bytes() == payload
    assert progress[-1] == (len(payload), len(payload))
    downloaded.unlink()
    directory.rmdir()
    serve(
        monkeypatch,
        {
            info.checksum_url: f"{'0' * 64}  {info.installer_name}\n".encode(),
            info.installer_url: payload,
        },
    )
    with pytest.raises(ValueError):
        updater.download_update(info, lambda *_: None)
    assert not directory.exists()


def test_duplicate_checksum_is_rejected_before_downloading(monkeypatch):
    data = release()
    serve(monkeypatch, {updater.RELEASE_API: json.dumps(data).encode()})
    info = updater.check_update("1.1.0")
    line = f"{'0' * 64}  {info.installer_name}\n"
    serve(monkeypatch, {info.checksum_url: (line * 2).encode()})
    with pytest.raises(ValueError, match="ambíguo"):
        updater.download_update(info, lambda *_: None)


def test_helper_waits_installs_and_restarts_in_order(tmp_path, monkeypatch):
    actions = []
    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"setup")
    monkeypatch.setattr(update_helper, "wait_for_parent", lambda pid: actions.append(("wait", pid)))
    monkeypatch.setattr(
        update_helper.subprocess,
        "run",
        lambda args, check: actions.append(("install", args)) or SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        update_helper.subprocess, "Popen", lambda args, close_fds: actions.append(("start", args))
    )
    update_helper.apply_update(123, installer, tmp_path)
    assert [action[0] for action in actions] == ["wait", "install", "start"]
    assert f"/DIR={tmp_path}" in actions[1][1]
    assert actions[2][1] == [str(tmp_path / "WinLink.exe")]
    assert not installer.exists()


def test_helper_never_restarts_after_installer_failure(tmp_path, monkeypatch):
    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"setup")
    monkeypatch.setattr(update_helper, "wait_for_parent", lambda pid: None)
    monkeypatch.setattr(
        update_helper.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1)
    )
    restart = Mock()
    monkeypatch.setattr(update_helper.subprocess, "Popen", restart)
    with pytest.raises(RuntimeError):
        update_helper.apply_update(123, installer, tmp_path)
    restart.assert_not_called()
    assert installer.exists()


def test_update_dialog_ignore_and_portable_fallback(qtbot, monkeypatch):
    parent = QWidget()
    qtbot.addWidget(parent)
    info = updater.UpdateInfo("1.2.0", "v1.2.0", updater.RELEASE_ROOT)
    dialog = UpdateDialog(info, parent)
    dialog.show()
    assert not dialog.install.isEnabled()
    assert "indisponível" in dialog.status.text()
    dialog.ignore.click()
    assert updater.ignored_version() == "1.2.0"
    assert not dialog.isVisible()


def test_verified_download_launches_helper_before_closing(qtbot, tmp_path, monkeypatch):
    parent = QWidget()
    parent._operation_active = False
    qtbot.addWidget(parent)
    parent.show()
    info = updater.UpdateInfo("1.2.0", "v1.2.0", updater.RELEASE_ROOT, "installer", "sums")
    installer = tmp_path / "setup.exe"
    calls = []
    monkeypatch.setattr(updater, "download_update", lambda info, progress: installer)
    monkeypatch.setattr(
        updater, "launch_helper", lambda path, root: calls.append((path, root, parent.isVisible()))
    )
    dialog = UpdateDialog(info, parent, tmp_path)
    dialog.show()
    dialog.install.click()
    qtbot.waitUntil(lambda: bool(calls))
    assert calls == [(installer, tmp_path, True)]
    assert not parent.isVisible()


def test_failed_download_keeps_application_open(qtbot, tmp_path, monkeypatch):
    parent = QWidget()
    parent._operation_active = False
    qtbot.addWidget(parent)
    parent.show()
    info = updater.UpdateInfo("1.2.0", "v1.2.0", updater.RELEASE_ROOT, "installer", "sums")

    def fail(*args):
        raise ValueError("bad checksum")

    monkeypatch.setattr(updater, "download_update", fail)
    launch = Mock()
    monkeypatch.setattr(updater, "launch_helper", launch)
    dialog = UpdateDialog(info, parent, tmp_path)
    dialog.show()
    dialog.install.click()
    qtbot.waitUntil(lambda: "Não foi possível" in dialog.status.text())
    assert parent.isVisible() and dialog.install.isEnabled() and dialog.later.isEnabled()
    launch.assert_not_called()

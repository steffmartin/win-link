"""Check GitHub releases and verify installers before handing them to the helper."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from winlink.core.config import get_appdata_path

RELEASE_API = "https://api.github.com/repos/steffmartin/win-link/releases/latest"
RELEASE_ROOT = "https://github.com/steffmartin/win-link/releases"
MAX_INSTALLER_SIZE = 256 * 1024 * 1024
MAX_METADATA_SIZE = 1024 * 1024
MAX_SUMS_SIZE = 65536
_VERSION = re.compile(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
_ALLOWED_REDIRECT_HOSTS = {
    "github.com",
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
}


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    tag: str
    release_url: str
    installer_url: str | None = None
    checksum_url: str | None = None

    @property
    def installer_name(self) -> str:
        return f"WinLink-Setup-{self.version}.exe"


def _version(value: object) -> tuple[int, int, int] | None:
    match = _VERSION.fullmatch(value) if isinstance(value, str) else None
    return tuple(map(int, match.groups())) if match else None  # type: ignore[return-value]


def _asset_url(url: object, tag: str, filename: str) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    try:
        return (
            parsed.scheme == "https"
            and parsed.hostname == "github.com"
            and parsed.port in (None, 443)
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and parsed.path == f"/steffmartin/win-link/releases/download/{tag}/{filename}"
        )
    except ValueError:
        return False


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        try:
            valid = (
                parsed.scheme == "https"
                and parsed.hostname in _ALLOWED_REDIRECT_HOSTS
                and parsed.port in (None, 443)
                and not parsed.username
                and not parsed.password
            )
        except ValueError:
            valid = False
        if not valid:
            raise URLError("Redirecionamento de atualização não permitido")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open(url: str, timeout: int = 10):
    request = Request(
        url,
        headers={"User-Agent": "WinLink-Updater", "Accept": "application/vnd.github+json"},
    )
    return build_opener(_SafeRedirect()).open(request, timeout=timeout)


def _read_limited(response, limit: int) -> bytes:
    length = response.headers.get("Content-Length")
    if length is not None and (not length.isdecimal() or int(length) > limit):
        raise ValueError("Tamanho de resposta inválido")
    data: bytes = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Resposta excede o limite")
    return data


def ignored_version() -> str:
    try:
        data = json.loads((get_appdata_path() / "update.json").read_text(encoding="utf-8"))
        value = data.get("ignoredVersion", "")
        return value if _version(value) else ""
    except (OSError, ValueError, AttributeError):
        return ""


def ignore_version(version: str) -> None:
    if _version(version) is None:
        raise ValueError("Versão inválida")
    path = get_appdata_path() / "update.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps({"ignoredVersion": version}) + "\n", encoding="utf-8")
    temporary.replace(path)


def check_update(current: str) -> UpdateInfo | None:
    installed = _version(current)
    if installed is None:
        return None
    with _open(RELEASE_API) as response:
        release = json.loads(_read_limited(response, MAX_METADATA_SIZE))
    tag = release.get("tag_name")
    latest = _version(tag)
    if (
        latest is None
        or latest <= installed
        or latest == _version(ignored_version())
        or release.get("draft")
        or release.get("prerelease")
    ):
        return None
    version = ".".join(map(str, latest))
    info = UpdateInfo(version, tag, f"{RELEASE_ROOT}/tag/{tag}")
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        return info
    selected = {}
    for asset in assets:
        if isinstance(asset, dict) and asset.get("name") in (info.installer_name, "SHA256SUMS.txt"):
            name = asset["name"]
            # Ambiguous release metadata must never select an arbitrary executable.
            if name in selected:
                return info
            selected[name] = asset.get("browser_download_url")
    installer = selected.get(info.installer_name)
    sums = selected.get("SHA256SUMS.txt")
    if _asset_url(installer, tag, info.installer_name) and _asset_url(sums, tag, "SHA256SUMS.txt"):
        return UpdateInfo(version, tag, info.release_url, installer, sums)
    return info


def installed_root() -> Path | None:
    if not getattr(sys, "frozen", False):
        return None
    root = Path(sys.executable).resolve().parent
    if (root / "winlink-installed.marker").is_file() and (
        root / "WinLinkUpdateHelper.exe"
    ).is_file():
        return root
    return None


def download_update(info: UpdateInfo, progress) -> Path:
    if not (
        _version(info.tag) == _version(info.version)
        and _asset_url(info.installer_url, info.tag, info.installer_name)
        and _asset_url(info.checksum_url, info.tag, "SHA256SUMS.txt")
    ):
        raise ValueError("Arquivos da release indisponíveis")
    assert info.checksum_url is not None and info.installer_url is not None
    with _open(info.checksum_url, timeout=30) as response:
        sums = _read_limited(response, MAX_SUMS_SIZE).decode("utf-8")
    matches = []
    for line in sums.splitlines():
        match = re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?([^\s]+)\s*", line)
        if match and match.group(2) == info.installer_name:
            matches.append(match.group(1).lower())
    if len(matches) != 1:
        raise ValueError("Checksum ausente ou ambíguo")
    directory = Path(tempfile.mkdtemp(prefix="winlink-update-"))
    target = directory / info.installer_name
    deadline = time.monotonic() + 300
    try:
        with _open(info.installer_url, timeout=30) as response, target.open("xb") as output:
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdecimal() or int(length) > MAX_INSTALLER_SIZE):
                raise ValueError("Tamanho do instalador inválido")
            total = int(length) if length else 0
            received = 0
            digest = hashlib.sha256()
            while chunk := response.read(1024 * 1024):
                if time.monotonic() > deadline:
                    raise TimeoutError("Download demorou demais")
                received += len(chunk)
                if received > MAX_INSTALLER_SIZE:
                    raise ValueError("Instalador excede o limite")
                digest.update(chunk)
                output.write(chunk)
                progress(received, total)
            if not received or (total and received != total) or digest.hexdigest() != matches[0]:
                raise ValueError("Verificação do instalador falhou")
        return target
    except Exception:
        target.unlink(missing_ok=True)
        directory.rmdir()
        raise


def discard_download(installer: Path) -> None:
    """Remove only files created in this updater's temporary directory."""
    if not installer.parent.name.startswith("winlink-update-"):
        return
    try:
        installer.unlink(missing_ok=True)
        installer.parent.rmdir()
    except OSError:
        pass


def launch_helper(installer: Path, root: Path) -> None:
    helper = installer.parent / "WinLinkUpdateHelper.exe"
    shutil.copyfile(root / helper.name, helper)
    try:
        subprocess.Popen(
            [str(helper), str(os.getpid()), str(installer), str(root)],
            close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        helper.unlink(missing_ok=True)
        raise

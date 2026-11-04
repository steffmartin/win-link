"""Validate the frozen bundle and a separately identified installer in the workspace.

Usage: python scripts/validate_distribution.py path/to/ISCC.exe
The production installer is never installed by this script.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build" / "distribution-test"
WORK.mkdir(parents=True, exist_ok=True)
DATA = WORK / "data"
INSTALL = WORK / "installed"
for path in (WORK, DATA, INSTALL):
    assert path.resolve().is_relative_to(ROOT)
DATA.mkdir(exist_ok=True)


def smoke(executable, name):
    report = WORK / f"{name}.json"
    environment = os.environ.copy()
    environment["APPDATA"] = str(WORK / "appdata")
    environment["WINLINK_SCAN_DIRECTORIES"] = "[]"
    environment["PATH"] = os.environ.get("SystemRoot", r"C:\Windows") + r"\System32"
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    subprocess.run(
        [str(executable), "--smoke-test", str(report)],
        env=environment,
        cwd=WORK,
        check=True,
        timeout=30,
    )
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["frozen"] and result["icon_loaded"] and result["window"] == "WinLink"
    assert result["navigation_icons"] and result["creation_icon"]
    assert report.with_suffix(".png").exists()
    assert result["status"].startswith("Escaneamento concluído")
    return result


results = {"portable": smoke(ROOT / "dist" / "WinLink" / "WinLink.exe", "portable")}
if len(sys.argv) > 1:
    compiler = Path(sys.argv[1]).resolve()
    subprocess.run(
        [
            str(compiler),
            "/DInstallerAppId=WinLink-Distribution-Validation",
            f"/DUserDataDir={DATA}",
            "/DOutputBase=WinLink-Validation-Setup",
            str(ROOT / "installer" / "winlink.iss"),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    installer = ROOT / "dist" / "WinLink-Validation-Setup.exe"
    payload = WORK / "payload"
    payload.mkdir(exist_ok=True)
    (payload / "preserve.txt").write_text("preserve", encoding="utf-8")
    link = WORK / "junction"
    if not link.is_junction():
        import _winapi

        _winapi.CreateJunction(str(payload), str(link))
    for delete_history in (False, True):
        subprocess.run(
            [
                str(installer),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/NOICONS",
                f"/DIR={INSTALL}",
            ],
            check=True,
            timeout=90,
        )
        results["installed"] = smoke(INSTALL / "WinLink.exe", "installed")
        for name in ("config.json", "cache.json", "history.json", "winlink.log"):
            (DATA / name).write_text("{}", encoding="utf-8")
        arguments = [
            str(INSTALL / "unins000.exe"),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
        ]
        if delete_history:
            arguments.append("/DELETEHISTORY")
        subprocess.run(arguments, check=True, timeout=90)
        # Inno's bootstrap uninstaller can return before its temporary child finishes.
        deadline = time.monotonic() + 20
        while (
            (INSTALL / "WinLink.exe").exists() or (DATA / "config.json").exists()
        ) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not (INSTALL / "WinLink.exe").exists()
        assert not (DATA / "config.json").exists()
        assert not (DATA / "cache.json").exists()
        assert not (DATA / "winlink.log").exists()
        assert (DATA / "history.json").exists() != delete_history
        assert link.is_junction() and (link / "preserve.txt").read_text() == "preserve"
    link.rmdir()
    results["installer"] = {
        "install": True,
        "uninstall_keep_history": True,
        "uninstall_delete_history": True,
        "junction_preserved": True,
    }
results["clean_machine"] = "not tested; host has Python installed"
(ROOT / "docs" / "validacao").mkdir(parents=True, exist_ok=True)
(ROOT / "docs" / "validacao" / "redesign-distribution.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
print(json.dumps(results, indent=2))

"""Small standalone Windows executable that updates after WinLink has exited."""

import ctypes
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path


def wait_for_parent(pid: int) -> None:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if not handle:
        if ctypes.get_last_error() == 87:  # The process already exited.
            return
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if kernel.WaitForSingleObject(handle, 120000) != 0:
            raise RuntimeError("O WinLink não encerrou a tempo.")
    finally:
        kernel.CloseHandle(handle)


def apply_update(pid: int, installer: Path, root: Path) -> None:
    wait_for_parent(pid)
    process = subprocess.run(
        [
            str(installer),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            f"/DIR={root}",
        ],
        check=False,
    )
    if process.returncode:
        raise RuntimeError(f"O instalador retornou o código {process.returncode}.")
    subprocess.Popen([str(root / "WinLink.exe")], close_fds=True)
    installer.unlink(missing_ok=True)


def main() -> int:
    try:
        if len(sys.argv) != 4:
            raise ValueError("Parâmetros de atualização inválidos.")
        apply_update(int(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
        return 0
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(
            None,
            f"Não foi possível concluir a atualização: {exc}\n"
            "Abra o WinLink novamente ou reinstale a versão desejada.",
            "WinLink",
            0x10,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

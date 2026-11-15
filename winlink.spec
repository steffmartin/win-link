# Build with: python -m PyInstaller --noconfirm winlink.spec
import os
import sys
from pathlib import Path
root = Path(SPECPATH)
# Dependency discovery must not pick unrelated ICU/UCRT DLLs from developer tools.
windows = Path(os.environ["SystemRoot"])
os.environ["PATH"] = os.pathsep.join([str(Path(sys.executable).parent),
                                    str(windows / "System32"), str(windows)])
a = Analysis([str(root / "src/winlink/main.py")], pathex=[str(root / "src")],
             binaries=[],
             datas=[(str(root / "LICENSE"), "."), (str(root / "resources/ui"), "ui")],
             hiddenimports=["win32timezone"],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=["pytest", "mypy"],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="WinLink", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=bool(os.environ.get("WINLINK_CONSOLE")),
          icon=str(root / "resources/winlink.ico"))
# The standalone helper is copied to a temporary directory before the installation
# is replaced; unlike the main onedir executable it must not depend on _internal.
helper_a = Analysis([str(root / "src/winlink/update_helper.py")], pathex=[str(root / "src")],
                    binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={},
                    runtime_hooks=[], excludes=["PyQt6", "pytest", "mypy"], noarchive=False)
helper_pyz = PYZ(helper_a.pure)
helper = EXE(helper_pyz, helper_a.scripts, helper_a.binaries, helper_a.datas, [],
             name="WinLinkUpdateHelper", debug=False, strip=False, upx=False, console=False,
             icon=str(root / "resources/winlink.ico"))
coll = COLLECT(exe, helper, a.binaries, a.datas, strip=False, upx=False, name="WinLink")

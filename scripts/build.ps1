param([string]$Iscc)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & .\.venv\Scripts\python.exe resources/icon.py
    if ($LASTEXITCODE) { throw 'Falha ao gerar ícone' }
    & .\.venv\Scripts\python.exe -m PyInstaller --noconfirm winlink.spec
    if ($LASTEXITCODE) { throw 'Falha no PyInstaller' }
    if ($Iscc) {
        & $Iscc installer/winlink.iss
        if ($LASTEXITCODE) { throw 'Falha no Inno Setup' }
    }
} finally { Pop-Location }

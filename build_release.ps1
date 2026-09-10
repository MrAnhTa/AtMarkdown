$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
}
& .venv/Scripts/python.exe -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Could not initialize pip.' }
& .venv/Scripts/python.exe -m pip install -r requirements.txt 'pyinstaller>=6.10,<7'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& .venv/Scripts/python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& .venv/Scripts/python.exe -m PyInstaller --clean --noconfirm AtMd.spec
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
Write-Host 'Unsigned Python app: dist/AtMd.exe'

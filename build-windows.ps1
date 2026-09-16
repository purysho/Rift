$ErrorActionPreference = 'Stop'
python -m pip install --upgrade pyinstaller pillow
python .\tools\make_icon.py
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Rift --icon assets/icon.ico rift_desktop.pyw
Write-Host "Built dist\Rift.exe"

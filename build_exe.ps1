# Build executable (EXE) for QARUN HOTEL using PyInstaller
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\build_exe.ps1

$ErrorActionPreference = 'Stop'

Write-Host "=== QARUN HOTEL - EXE Build ==="

# Move to script directory
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# Ensure venv exists
if (-not (Test-Path ".venv/Scripts/python.exe")) {
    Write-Host "Creating virtual environment (.venv)..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    } else {
        python -m venv .venv
    }
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

# Ensure pip updated and install build deps
python -m pip install --upgrade pip
pip install -r requirements.txt
# Install PyInstaller (build-time only)
pip install pyinstaller

# Clean previous build
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist

# Compose add-data entries (Windows uses ';' separator)
$addData = @(
    "hotel\\templates;hotel\\templates",
    "hotel\\static;hotel\\static",
    "instance;instance",
    ".env;."
)

# Optional: include fonts directory if needed at runtime
if (Test-Path "fonts") {
    $addData += "fonts;fonts"
}

Write-Host "Preparing PyInstaller arguments..."
$args = @('--noconfirm','--clean','--name','QarunHotel','--onefile','--windowed')
if (Test-Path "hotel\\static\\favicon.ico") { $args += @('--icon','hotel\\static\\favicon.ico') }
foreach ($item in $addData) { $args += @('--add-data', $item) }
$args += 'run.py'

Write-Host "Running PyInstaller..."
& pyinstaller @args

# Copy helpful files to dist
if (Test-Path ".\dist\QarunHotel.exe") {
    $readme = @'
QarunHotel.exe - End-user portable app
Steps:
1) Run QarunHotel.exe
2) Open in browser: http://127.0.0.1:5000
Notes:
- Keep the "instance" folder if you ship hotel.db
- .env (if present) will be read automatically
'@
    $readme += "`r`nBuild time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $readme | Out-File -Encoding UTF8 .\dist\READ_ME_FIRST.txt
}

Write-Host "Build complete. Check the 'dist' folder."

@echo off
chcp 65001 >nul
title Download Python 3.11.4
color 0a

:start
cls
echo ====================================
echo    Downloading Python 3.11.4
echo ====================================
echo.

echo [*] Downloading Python 3.11.4 Installer...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe', 'python_installer.exe')"

if exist "python_installer.exe" (
    echo [*] Download completed successfully!
    echo.
    echo [*] Starting Python installer...
    echo [*] Please follow these steps:
    echo [1] Check "Add Python 3.11 to PATH" at the bottom
    echo [2] Click "Install Now"
    echo [3] Wait for installation to complete
    echo [4] Click "Close" when done
    echo.
    echo [*] After installation, run: run_system.bat
    echo.
    start "" python_installer.exe
) else (
    echo [!] Failed to download Python installer
    echo [*] Please download it manually from:
    echo [*] https://www.python.org/downloads/release/python-3114/
    pause
)

exit /b 0

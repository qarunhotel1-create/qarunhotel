@echo off
chcp 65001 >nul
title Simple Python Installer
color 0a

:start
cls
echo ====================================
echo    Simple Python 3.11.4 Installer
echo ====================================
echo.

set PYTHON_URL=https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe
set INSTALLER=python_installer.exe

echo [*] Downloading Python 3.11.4...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%PYTHON_URL%', '%INSTALLER%')"

if not exist "%INSTALLER%" (
    echo [!] Failed to download Python
    echo [*] Please download it manually from:
    echo [*] https://www.python.org/downloads/release/python-3114/
    pause
    exit /b 1
)

echo [*] Starting Python installer...
echo.
echo [*] Important: In the installer:
echo [1] Check "Add Python 3.11 to PATH" at the bottom
echo [2] Click "Install Now"
echo [3] Wait for installation

echo.
echo [*] After installation completes, run: run_system.bat
echo.

start "" "%INSTALLER%"

timeout /t 10 >nul
del /f /q "%INSTALLER%" 2>nul

exit /b 0

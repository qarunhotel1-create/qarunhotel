@echo off
title Scanner Bridge for Kyocera FS-3540MFP KX
color 0A

echo ========================================
echo   Scanner Bridge for Kyocera FS-3540MFP KX
echo ========================================
echo.

echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python found!
echo [INFO] Starting Scanner Bridge...
echo.

cd /d "%~dp0"
python scan_agent/scan_agent.py

echo.
echo [INFO] Scanner Bridge stopped.
pause

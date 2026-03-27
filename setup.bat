@echo off
chcp 65001 >nul
title QARUN HOTEL - Setup
color 0a
cls

echo ====================================
echo    QARUN HOTEL - Setup Wizard
echo ====================================
echo.

echo [*] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Python is already installed.
    goto :install_requirements
)

echo [*] Python is not installed. Downloading Python installer...

REM Download Python installer
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe', 'python_installer.exe')"

if not exist "python_installer.exe" (
    echo [!] Failed to download Python installer
    echo [*] Please download Python manually from:
    echo [*] https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [*] Installing Python (this may take a few minutes)...
start /wait "" python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

del /f /q python_installer.exe 2>nul

:install_requirements
call :check_python
if %ERRORLEVEL% NEQ 0 (
    pause
    exit /b 1
)

echo [*] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to create virtual environment
    pause
    exit /b 1
)

echo [*] Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to install requirements
    pause
    exit /b 1
)

echo.
echo [*] Setup completed successfully!
echo [*] Starting the hotel management system...

timeout /t 2 >nul
start "" "run_simple.bat"

exit /b 0

:check_python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python installation failed or not in PATH
    echo [*] Please restart your computer and run this setup again
    echo [*] Or install Python manually from:
    echo [*] https://www.python.org/downloads/
    echo [*] Make sure to check "Add Python to PATH" during installation
    exit /b 1
)
exit /b 0

@echo off
chcp 65001 >nul
title Python 3.11.4 Portable Setup
color 0a

:start
cls
echo ====================================
echo    Python 3.11.4 Portable Setup
echo ====================================
echo.

set PYTHON_DIR=Python311
set ZIP_FILE=python-3.11.4-embed-amd64.zip

if exist "%PYTHON_DIR%\python.exe" (
    echo [*] Python is already installed in %PYTHON_DIR%
    goto :setup_complete
)

echo [*] Creating Python directory...
mkdir %PYTHON_DIR% 2>nul

if not exist "%ZIP_FILE%" (
    echo [*] Downloading Python 3.11.4 (Embeddable)...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-embed-amd64.zip', '%ZIP_FILE%')"
    
    if not exist "%ZIP_FILE%" (
        echo [!] Failed to download Python
        pause
        exit /b 1
    fi
)

echo [*] Extracting Python...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%PYTHON_DIR%' -Force"

echo [*] Setting up Python...
cd %PYTHON_DIR%
echo import site >> python311._pth
cd ..

echo [*] Installing pip...
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
%PYTHON_DIR%\python.exe get-pip.py

del get-pip.py 2>nul

:setup_complete
echo.
echo [*] Python 3.11.4 Portable is ready!
echo [*] Python path: %~dp0%PYTHON_DIR%
echo.

:run_system
if not exist "venv" (
    echo [*] Creating virtual environment...
    %PYTHON_DIR%\python.exe -m venv venv
)

call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [*] Installing requirements...
pip install flask flask-sqlalchemy flask-login flask-migrate flask-wtf python-dotenv reportlab

if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to install requirements
    pause
    exit /b 1
)

start http://localhost:5000
python run.py

pause

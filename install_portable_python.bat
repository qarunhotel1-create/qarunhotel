@echo off
chcp 65001 >nul
title Python 3.11.4 Portable Installer
color 0a

set PYTHON_ZIP=python-3.11.4-embed-amd64.zip
set PYTHON_DIR=Python311

:start
cls
echo ====================================
echo    Python 3.11.4 Portable Installer
echo ====================================
echo.

if exist "%PYTHON_DIR%\python.exe" (
    echo [*] Python is already installed in %PYTHON_DIR%
    goto :install_pip
)

echo [*] Downloading Python 3.11.4 (Embeddable)...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-embed-amd64.zip', '%PYTHON_ZIP%')"

if not exist "%PYTHON_ZIP%" (
    echo [!] Failed to download Python
    echo [*] Please download it manually from:
    echo [*] https://www.python.org/ftp/python/3.11.4/python-3.11.4-embed-amd64.zip
    echo [*] And place it in the current directory
    pause
    exit /b 1
)

echo [*] Extracting Python...
mkdir %PYTHON_DIR% 2>nul
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"

del /f /q "%PYTHON_ZIP%" 2>nul

:install_pip
echo [*] Setting up pip...
cd %PYTHON_DIR%
echo import site >> python311._pth
cd ..

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
%PYTHON_DIR%\python.exe get-pip.py

del get-pip.py 2>nul

:create_venv
echo [*] Creating virtual environment...
%PYTHON_DIR%\python.exe -m venv venv

:install_requirements
echo [*] Installing requirements...
call venv\Scripts\activate.bat
pip install flask flask-sqlalchemy flask-login flask-migrate flask-wtf python-dotenv reportlab

:run_system
echo [*] Starting the system...
start http://localhost:5000
python run.py

pause

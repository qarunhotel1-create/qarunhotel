@echo off
chcp 65001 >nul
title QARUN HOTEL - Server
color 0a

:start
cls
echo ====================================
echo    QARUN HOTEL Management System
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Get IP address
for /f "tokens=14 delims= " %%i in ('ipconfig ^| findstr "IPv4" ^| findstr /v "127.0.0.1"') do set IP=%%i

if "%IP%"=="" (
    set IP=127.0.0.1
)

cls
echo ====================================
echo    QARUN HOTEL Management System
echo ====================================
echo.
echo [*] Starting server...
echo.
echo [*] Access the system from any device on the network:
echo [*] http://%IP%:5000
echo.
echo [*] Or from this computer:
echo [*] http://localhost:5000
echo.
echo [*] Default login:
echo [*] Username: admin
echo [*] Password: admin
echo.
echo ====================================
echo.

REM Run the server
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Error starting server
    echo [*] Make sure all requirements are installed
    echo [*] Run: install_requirements.bat
    echo.
    pause
    exit /b 1
)

echo.
echo [*] Server stopped. Press any key to restart or close to exit...
pause >nul
goto start

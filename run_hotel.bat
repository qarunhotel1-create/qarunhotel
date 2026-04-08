@echo off
chcp 65001 >nul
title QARUN HOTEL - Direct Run
color 0a

:start
cls
echo ====================================
echo    QARUN HOTEL - Direct Run
echo ====================================
echo.

echo [*] Starting the system...
start http://localhost:5000
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Failed to start the system
    echo [*] Make sure Python 3.11 is installed and added to PATH
    echo [*] You can download it from:
    echo [*] https://www.python.org/downloads/release/python-3114/
    echo.
    pause
    exit /b 1
)

goto start

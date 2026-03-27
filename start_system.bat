@echo off
REM Unified starter for QARUN HOTEL on Windows
REM - Detect or create virtual environment (.venv preferred)
REM - Upgrade pip and install requirements
REM - Run run.py

setlocal enableextensions enabledelayedexpansion
cd /d "%~dp0"

echo ===============================
echo   Starting QARUN HOTEL System
echo ===============================

REM Prefer .venv, fallback to venv
set "VENV_DIR=.venv"
if exist ".venv\Scripts\python.exe" goto :venv_found
if exist "venv\Scripts\python.exe" set "VENV_DIR=venv" & goto :venv_found

echo Virtual environment not found. Creating .venv ...
where py >nul 2>&1 && (py -3 -m venv .venv) || (python -m venv .venv)
if exist ".venv\Scripts\python.exe" (
    set "VENV_DIR=.venv"
) else (
    echo Failed to create virtual environment. Please ensure Python is installed and on PATH.
    pause
    exit /b 1
)

:venv_found
echo Using virtual environment: %VENV_DIR%
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip

if exist requirements.txt (
    echo Installing requirements from requirements.txt ...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Skipping dependencies install.
)

echo Launching application (run.py)...
python run.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo Application exited with code %RC%.
    echo Press any key to close.
    pause >nul
)

endlocal

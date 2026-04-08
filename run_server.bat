@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

rem --- Simplified Python Selection ---
set "PYTHON="
if exist "venv_fixed\Scripts\python.exe" (
    set "PYTHON=venv_fixed\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
) else if exist "Python311\python.exe" (
    set "PYTHON=Python311\python.exe"
) else (
    set "PYTHON=python"
)

echo Using Python at: %PYTHON%

rem --- Set Host and Port ---
set "HOST=0.0.0.0"
set "PORT=5000"

echo Starting server on %HOST%:%PORT%...

rem --- Run the Server ---
"%PYTHON%" "run.py"

endlocal
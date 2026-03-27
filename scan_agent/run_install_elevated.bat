@echo off
REM Double-click this file to run the install_and_run_agent.ps1 script with admin privileges.
REM It will prompt for UAC elevation.
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_and_run_agent.ps1"' -Verb RunAs"
pause

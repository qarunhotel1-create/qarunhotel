@echo off
title Scanner Integration Test
color 0B

echo ========================================
echo   Scanner Integration Test
echo ========================================
echo.

echo [INFO] Opening scanner test page...
start "" "test_scanner_integration.html"

echo.
echo [INFO] Test page opened in default browser
echo [INFO] Make sure Scanner Bridge is running first!
echo.

pause

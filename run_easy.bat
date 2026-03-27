@echo off
chcp 65001 >nul
title QARUN HOTEL - Easy Start
color 0a

:start
cls
echo ====================================
echo    QARUN HOTEL - Easy Start
echo ====================================
echo.

echo [*] جاري تشغيل النظام...
echo.
echo [*] إذا لم يعمل النظام، يرجى تثبيت Python يدويًا من:
echo [*] https://www.python.org/downloads/
echo [*] مع تفعيل خيار "Add Python to PATH"
echo.

timeout /t 3 >nul

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python غير مثبت أو غير مضاف إلى PATH
    start https://www.python.org/downloads/
    echo.
    echo [*] سيتم فتح صفحة تحميل Python
    echo [*] بعد التثبيت، شغل هذا الملف مرة أخرى
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo [*] جاري إعداد النظام لأول مرة...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

start http://localhost:5000
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] فشل في تشغيل النظام
    echo [*] جرب تشغيل الملف كمسؤول (Run as Administrator)
    pause
)

goto start

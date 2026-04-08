@echo off
chcp 65001 >nul
title QARUN HOTEL - System Fix
color 0a

:start
cls
echo ====================================
echo    QARUN HOTEL - System Fix
echo ====================================
echo.

echo [*] جاري إصلاح النظام...
echo.

echo [1] تثبيت Python 3.11
if exist "%ProgramFiles%\Python311\python.exe" (
    echo [*] Python 3.11 مثبت بالفعل
) else (
    echo [*] جاري تحميل Python 3.11...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe', 'python_installer.exe')"
    
    if exist "python_installer.exe" (
        echo [*] جاري التثبيت...
        start /wait "" python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del /f /q python_installer.exe
    ) else (
        echo [!] فشل في تحميل Python
        echo [*] يرجى تحميله يدويًا من:
        echo [*] https://www.python.org/downloads/release/python-3114/
        pause
        exit /b 1
    )
)

echo.
echo [2] إعداد البيئة الافتراضية...
"%ProgramFiles%\Python311\python.exe" -m venv venv
call venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في إنشاء البيئة الافتراضية
    pause
    exit /b 1
)

echo.
echo [3] تثبيت المتطلبات...
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-login flask-migrate flask-wtf python-dotenv reportlab

if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تثبيت المتطلبات
    pause
    exit /b 1
)

echo.
echo [4] إعداد قاعدة البيانات...
python -c "from hotel import db; from hotel.models.user import User; db.create_all()"

echo.
echo [*] تم إصلاح النظام بنجاح!
echo [*] يمكنك الآن تشغيل النظام من خلال ملف run_easy.bat
echo.
pause

exit /b 0

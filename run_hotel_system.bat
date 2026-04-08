@echo off
chcp 65001 >nul
title QARUN HOTEL - Server
color 0a
cls

echo ====================================
echo    QARUN HOTEL Management System
echo    Server Starting...
echo ====================================
echo.

REM التحقق من وجود البيئة الافتراضية
if not exist "venv\Scripts\activate.bat" (
    echo [*] البيئة الافتراضية غير موجودة، جاري التهيئة...
    call install_requirements.bat
    if %ERRORLEVEL% NEQ 0 (
        pause
        exit /b 1
    )
)

REM تفعيل البيئة الافتراضية
call venv\Scripts\activate.bat

REM الحصول على عنوان IP
for /f "tokens=14 delims= " %%i in ('ipconfig ^| findstr "IPv4" ^| findstr /v "127.0.0.1"') do set IP=%%i

if "%IP%"=="" (
    set IP=127.0.0.1
)

cls
echo ====================================
echo    QARUN HOTEL Management System
echo ====================================
echo.
echo [*] جاري تشغيل السيرفر...
echo.
echo [*] يمكن الوصول للنظام من أي جهاز على الشبكة باستخدام:
echo [*] http://%IP%:5000
echo.
echo [*] أو من الجهاز الحالي:
echo [*] http://localhost:5000
echo.
echo [*] بيانات الدخول الافتراضية:
echo [*] اسم المستخدم: admin
echo [*] كلمة المرور: admin
echo.
echo ====================================
echo.

REM تعيين متغيرات البيئة
echo [*] جاري تهيئة النظام...
set FLASK_APP=run.py
set FLASK_ENV=development
set HOST=0.0.0.0
set PORT=5000

REM تشغيل السيرفر
python -m flask run --host=%HOST% --port=%PORT%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] حدث خطأ أثناء تشغيل السيرفر
    echo [*] تأكد من تثبيت Python والمكتبات المطلوبة
    echo [*] قم بتشغيل: install_requirements.bat
    echo.
    pause
)

pause

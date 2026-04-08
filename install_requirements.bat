@echo off
title تثبيت متطلبات النظام
color 0a

echo ====================================
echo    تثبيت متطلبات QARUN HOTEL
echo ====================================
echo.

REM التحقق من تثبيت بايثون
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python غير مثبت على النظام
    echo [*] يرجى تحميل وتثبيت Python من الموقع الرسمي:
    echo [*] https://www.python.org/downloads/
    echo [*] تأكد من تفعيل خيار "Add Python to PATH" أثناء التثبيت
    pause
    exit /b 1
)

REM إنشاء بيئة افتراضية جديدة
echo [*] إنشاء بيئة افتراضية جديدة...
python -m venv venv

if not exist "venv\Scripts\activate.bat" (
    echo [!] فشل في إنشاء البيئة الافتراضية
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM تحديث pip
echo [*] تحديث pip...
python -m pip install --upgrade pip

REM تثبيت المتطلبات
echo [*] تثبيت حزم بايثون المطلوبة...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تثبيت المتطلبات
    pause
    exit /b 1
)

echo.
echo [√] تم تثبيت المتطلبات بنجاح!
echo.
pause

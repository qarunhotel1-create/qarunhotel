@echo off
chcp 65001 >nul
title QARUN HOTEL - Quick Fix
color 0a

:start
cls
echo ====================================
echo    QARUN HOTEL - Quick Fix
echo ====================================
echo.

echo [*] جاري إصلاح النظام السريع...
echo.

REM حذف البيئة القديمة إذا وجدت
if exist "venv" (
    echo [*] حذف البيئة الافتراضية القديمة...
    rmdir /s /q venv
)

REM إنشاء بيئة افتراضية جديدة
echo [*] إنشاء بيئة افتراضية جديدة...
"%ProgramFiles%\Python311\python.exe" -m venv venv

if not exist "venv\Scripts\activate.bat" (
    echo [!] فشل في إنشاء البيئة الافتراضية
    echo [*] تأكد من تثبيت Python 3.11 بشكل صحيح
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تفعيل البيئة الافتراضية
    pause
    exit /b 1
)

echo [*] تثبيت المتطلبات الأساسية...
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-login flask-migrate flask-wtf python-dotenv reportlab

if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تثبيت المتطلبات
    pause
    exit /b 1
)

echo.
echo [*] تم الإصلاح بنجاح!
echo [*] جاري تشغيل النظام...
echo.
timeout /t 2 >nul

start http://localhost:5000
python run.py

exit /b 0

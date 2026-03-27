@echo off
title فندق قارون - تشغيل النظام الأصلي
color 0A

echo.
echo ========================================
echo        🏨 فندق قارون - النظام الأصلي
echo ========================================
echo.

echo 🔍 تشخيص النظام...

echo 1. فحص Python...
python --version
if errorlevel 1 (
    echo ❌ Python غير متاح
    pause
    exit
)

echo 2. فحص Flask...
python -c "import flask; print('Flask:', flask.__version__)"
if errorlevel 1 (
    echo ❌ Flask غير مثبت
    echo تثبيت Flask...
    pip install flask flask-sqlalchemy flask-login flask-wtf flask-migrate python-dotenv
)

echo 3. محاولة تشغيل النظام...
python run.py

pause

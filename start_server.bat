@echo off
title QARUN HOTEL - Server
color 0a

echo ====================================
echo    QARUN HOTEL Management System
echo    Server Starting...
echo ====================================

REM الحصول على عنوان IP المحلي
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    for /f "tokens=*" %%b in ("%%a") do set "IP=%%b"
)

echo.
echo [*] جاري تشغيل السيرفر...
echo [*] يمكن الوصول للنظام من أي جهاز على الشبكة باستخدام:
echo [*] http://%IP%:5000
echo.
echo [*] بيانات الدخول الافتراضية:
echo [*] اسم المستخدم: admin
echo [*] كلمة المرور: admin
echo.
echo ====================================
echo.

REM تشغيل السيرفر
python run.py

REM في حالة حدوث خطأ
if errorlevel 1 (
    echo.
    echo [!] حدث خطأ أثناء تشغيل السيرفر
    echo [*] تأكد من تثبيت Python والمكتبات المطلوبة
    echo [*] قم بتشغيل: pip install -r requirements.txt
    echo.
    pause
)

pause

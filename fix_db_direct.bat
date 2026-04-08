@echo off
echo إصلاح قاعدة البيانات - إضافة حقول الحظر
echo =====================================

REM البحث عن Python
where python >nul 2>&1
if %errorlevel% == 0 (
    echo تم العثور على Python
    python fix_customer_block_db.py
    goto end
)

where py >nul 2>&1
if %errorlevel% == 0 (
    echo تم العثور على py
    py fix_customer_block_db.py
    goto end
)

where python3 >nul 2>&1
if %errorlevel% == 0 (
    echo تم العثور على python3
    python3 fix_customer_block_db.py
    goto end
)

echo لم يتم العثور على Python
echo يرجى تشغيل الأوامر التالية يدوياً:
echo.
echo 1. افتح قاعدة البيانات instance\hotel.db باستخدام أي أداة SQLite
echo 2. قم بتشغيل الأوامر الموجودة في ملف fix_db_manual.sql
echo.

:end
pause

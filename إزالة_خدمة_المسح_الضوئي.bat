@echo off
chcp 65001 > nul
title إزالة خدمة وكيل المسح الضوئي
color 0C

echo ========================================
echo   إزالة خدمة وكيل المسح الضوئي
echo   Kyocera FS-3540MFP KX
echo ========================================
echo.

:: التحقق من صلاحيات المسؤول
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] يجب تشغيل هذا الملف بصلاحيات المسؤول
    echo.
    echo الرجاء النقر بزر الماوس الأيمن على هذا الملف واختيار "تشغيل كمسؤول"
    echo.
    echo اضغط أي مفتاح للخروج...
    pause >nul
    exit /b 1
)

echo [تحذير] هذا الملف سيقوم بإزالة خدمة وكيل المسح الضوئي من النظام.
echo سيتوقف المسح الضوئي عن العمل تلقائياً عند بدء تشغيل النظام.
echo.
echo هل أنت متأكد من رغبتك في إزالة الخدمة؟
echo.
echo اضغط Y للاستمرار أو أي مفتاح آخر للإلغاء...

setlocal enabledelayedexpansion
set /p CONFIRM=
if /i "!CONFIRM!" neq "Y" (
    echo.
    echo تم إلغاء العملية.
    echo.
    echo اضغط أي مفتاح للخروج...
    pause >nul
    exit /b 0
)

echo.
echo [معلومات] جاري إيقاف خدمة وكيل المسح الضوئي...
net stop "ScannerBridge" >nul 2>&1

echo [معلومات] جاري إزالة خدمة وكيل المسح الضوئي...

if exist "%~dp0tools\nssm.exe" (
    "%~dp0tools\nssm.exe" remove "ScannerBridge" confirm
) else (
    sc delete "ScannerBridge" >nul 2>&1
)

echo [معلومات] جاري إزالة قاعدة جدار الحماية...
netsh advfirewall firewall delete rule name="Scanner Bridge Service" >nul 2>&1

echo.
echo [معلومات] تم إزالة خدمة وكيل المسح الضوئي بنجاح!
echo.
echo لإعادة تثبيت الخدمة، قم بتشغيل ملف "تثبيت_وكيل_المسح_كخدمة.bat"
echo.
echo اضغط أي مفتاح للخروج...
pause >nul
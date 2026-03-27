@echo off
chcp 65001 >nul
title Python Installation
color 0a
cls

echo ====================================
echo    Python Installation - QARUN HOTEL
echo ====================================
echo.

echo [*] جاري تثبيت Python من Microsoft Store...
start ms-windows-store://pdp/?productid=9PJPW5LDXLZ5

echo [*] يرجى الانتظار حتى يفتح متجر Microsoft Store...
timeout /t 5 >nul

echo.
echo [*] تعليمات التثبيت:
echo [1] انقر على "Get" أو "Install"
echo [2] انتظر حتى يكتمل التثبيت
echo [3] أغلق نافذة المتجر بعد اكتمال التثبيت
echo [4] أعد تشغيل الكمبيوتر بعد الانتهاء
echo.
echo [*] بعد إعادة التشغيل، شغل ملف run_simple.bat

timeout /t 10 >nul

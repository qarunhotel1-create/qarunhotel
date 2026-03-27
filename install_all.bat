@echo off
chcp 65001 >nul
title QARUN HOTEL - Auto Installer
color 0a
cls

echo ====================================
echo    QARUN HOTEL - Auto Installer
echo ====================================
echo.

echo [*] جاري التثبيت التلقائي الكامل...
echo [*] يرجى الانتظار ولا تغلق النافذة...
echo.

REM إنشاء مجلد التحميلات
if not exist "%USERPROFILE%\Downloads\QarunHotel_Install" (
    mkdir "%USERPROFILE%\Downloads\QarunHotel_Install"
)

REM تحميل Python
if not exist "%USERPROFILE%\Downloads\QarunHotel_Install\python_installer.exe" (
    echo [*] جاري تحميل Python...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe', '%USERPROFILE%\Downloads\QarunHotel_Install\python_installer.exe')"
)

REM تثبيت Python
if exist "%USERPROFILE%\Downloads\QarunHotel_Install\python_installer.exe" (
    echo [*] جاري تثبيت Python...
    start /wait "" "%USERPROFILE%\Downloads\QarunHotel_Install\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    echo [*] جاري إعداد متغيرات النظام...
    setx PATH "%PATH%;C:\Program Files\Python311\;C:\Program Files\Python311\Scripts\" /M
) else (
    echo [!] فشل في تحميل Python
    pause
    exit /b 1
)

REM إنشاء اختصار على سطح المكتب
if not exist "%USERPROFILE%\Desktop\QARUN HOTEL.lnk" (
    echo [*] جاري إنشاء اختصار على سطح المكتب...
    echo [InternetShortcut] > "%USERPROFILE%\Desktop\QARUN HOTEL.url"
    echo URL=file:///%~dp0run_final.bat >> "%USERPROFILE%\Desktop\QARUN HOTEL.url"
    echo IconIndex=0 >> "%USERPROFILE%\Desktop\QARUN HOTEL.url"
    echo IconFile=%%SystemRoot%%\System32\SHELL32.dll,15 >> "%USERPROFILE%\Desktop\QARUN HOTEL.url"
)

echo.
echo [*] تم الانتهاء من التثبيت!
echo [*] سيتم فتح النظام تلقائياً بعد 5 ثوانٍ...

timeout /t 5 >nul

REM تشغيل النظام
echo [*] جاري تشغيل النظام...
start "" "run_final.bat"

exit /b 0

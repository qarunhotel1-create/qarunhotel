@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion
title فندق قارون - تشغيل سيرفر مباشر وثابت
color 0A

cd /d "%~dp0"

echo ================================================
echo        مرحباً بك في نظام فندق قارون
echo   تشغيل سيرفر مباشر على الشبكة المحلية
echo ================================================

rem اختيار Python من بيئات افتراضية أو النسخة المرفقة
set "PYTHON="
if exist "venv_fixed\Scripts\python.exe" set "PYTHON=venv_fixed\Scripts\python.exe"
if not defined PYTHON if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"
if not defined PYTHON if exist "venv_new\Scripts\python.exe" set "PYTHON=venv_new\Scripts\python.exe"
if not defined PYTHON if exist "Python311\python.exe" set "PYTHON=Python311\python.exe"
if not defined PYTHON set "PYTHON=python"

rem فحص Python
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python غير متاح. يرجى تثبيت بايثون أو تشغيل setup.bat
    pause
    goto :eof
)

rem فحص Flask
"%PYTHON%" -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Flask غير مثبت. تثبيت المتطلبات...
    if exist "requirements.txt" (
        "%PYTHON%" -m pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ فشل تثبيت المتطلبات. تحقق من الاتصال بالإنترنت والصلاحيات.
            pause
            goto :eof
        )
    ) else (
        echo ❌ ملف requirements.txt غير موجود.
        pause
        goto :eof
    )
)

rem التحقق من صلاحيات المسؤول
set "ISADMIN=0"
net session >nul 2>&1
if %errorlevel%==0 set "ISADMIN=1"

rem محاولة فتح منفذ 5000 في الجدار الناري على الشبكات الخاصة/النطاق
if "%ISADMIN%"=="1" (
    echo فتح منفذ 5000 في جدار الحماية (Private/Domain)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Try { $name='QarunHotel HTTP 5000'; $existing=Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue; if($existing){Remove-NetFirewallRule -DisplayName $name -Confirm:$false}; New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5000 -Profile Domain,Private | Out-Null } Catch { exit 1 }"
) else (
    echo ⚠️ يُفضّل تشغيل هذا الملف كمسؤول (Run as Administrator) لفتح منفذ 5000 في جدار الحماية.
)

echo.
echo عناوين IP المتاحة على هذا الجهاز (الشبكات المفعلة فقط):
powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.InterfaceOperationalStatus -eq 'Up' -and $_.InterfaceAlias -notmatch 'vEthernet|Virtual|Loopback|Hyper-V|VMware|VPN|Tailscale' } ^| ForEach-Object { '{0,-20} {1}' -f $_.InterfaceAlias, $_.IPAddress }"

echo.
echo روابط الوصول المحتملة من الهاتف:
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.InterfaceOperationalStatus -eq 'Up' -and $_.InterfaceAlias -notmatch 'vEthernet|Virtual|Loopback|Hyper-V|VMware|VPN|Tailscale' } ^| Select-Object -ExpandProperty IPAddress"`) do (
    echo  - http://%%I:5000
)

echo.
echo يمكن الوصول محلياً: http://localhost:5000
echo بيانات الدخول الافتراضية:
echo اسم المستخدم: admin@example.com
echo كلمة المرور: admin123
echo ================================================

rem التحقق من أن المنفذ غير مستخدم
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo ⚠️ المنفذ 5000 قيد الاستخدام. قد يكون السيرفر قيد التشغيل بالفعل.
)

echo جاري تشغيل السيرفر...

set "HOST=0.0.0.0"
set "PORT=5000"

"%PYTHON%" "run.py"
if errorlevel 1 (
    echo.
    echo ❌ حدث خطأ أثناء تشغيل السيرفر.
    echo حاول: "%PYTHON%" -m pip install -r requirements.txt
    echo أو تشغيل: install_requirements.bat
    echo.
    pause
    goto :eof
)

echo.
pause
endlocal
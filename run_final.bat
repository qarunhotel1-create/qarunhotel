@echo off
chcp 65001 >nul
title QARUN HOTEL - Final Solution
color 0a

:start
cls
echo ====================================
echo    QARUN HOTEL - Final Solution
echo ====================================
echo.

echo [1] تثبيت Python (للمرة الأولى فقط)
echo [2] تشغيل النظام
echo [3] تحديث النظام
echo [4] الخروج
echo.
set /p choice=اختر رقم الإجراء المطلوب: 

if "%choice%"=="1" goto install_python
if "%choice%"=="2" goto run_system
if "%choice%"=="3" goto update_system
if "%choice%"=="4" exit /b

goto start

:install_python
start "" "install_python.bat"
goto start

:run_system
if not exist "venv\Scripts\activate.bat" (
    echo [*] جاري إعداد النظام لأول مرة...
    call :setup_venv
) else (
    call venv\Scripts\activate.bat
)

if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تشغيل النظام
    pause
    exit /b 1
)

python run.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تشغيل السيرفر
    pause
)

goto start

:update_system
if exist "venv" rmdir /s /q venv
call :setup_venn
goto start

:setup_venv
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل في تثبيت المتطلبات
    pause
    exit /b 1
)
echo [*] تم إعداد النظام بنجاح!
timeout /t 2 >nul
:end
cls
goto start

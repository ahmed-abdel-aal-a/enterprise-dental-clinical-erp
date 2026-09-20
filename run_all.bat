@echo off
chcp 65001 > nul
echo ==========================================================
echo        🚀 DentApex Enterprise - All-in-One Runner
echo ==========================================================
cd /d "%~dp0"

echo [1/4] إيقاف أي عمليات سابقة على البورتين 8000 و 3000...
call stop_all.bat

echo.
echo [2/4] تشغيل خادم الباك إند (Port 8000)...
start "DentApex Enterprise - Backend [Port 8000]" cmd /k "call start_backend.bat"

echo انتظار استقرار خادم الباك إند...
timeout /t 3 /nobreak > nul

echo.
echo [3/4] تشغيل خادم الفرونت إند (Port 3000)...
start "DentApex Enterprise - Frontend [Port 3000]" cmd /k "call start_frontend.bat"

echo انتظار استقرار خادم الفرونت إند...
timeout /t 4 /nobreak > nul

echo.
echo [4/4] فتح النظام في المتصفح...
start http://127.0.0.1:3000

echo ==========================================================
echo  ✅ تم تشغيل نظام DentApex Enterprise بنجاح تام!
echo  - الباك إند: http://127.0.0.1:8000
echo  - فحص الصحة: http://127.0.0.1:8000/health
echo  - الواجهة الأمامية: http://127.0.0.1:3000
echo ==========================================================

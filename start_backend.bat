@echo off
chcp 65001 > nul
echo ==========================================================
echo [DentApex Enterprise] تشغيل خادم الباك إند (FastAPI / Uvicorn)...
echo ==========================================================
cd /d "%~dp0dentalpin-main\backend"

if not exist "venv\Scripts\python.exe" (
    echo [خطأ] البيئة الافتراضية venv غير موجودة في dentalpin-main\backend\venv!
    pause
    exit /b 1
)

echo جاري بدء Uvicorn على المنفذ 8000...
echo الرابط المباشر: http://127.0.0.1:8000
echo فحص الحالة: http://127.0.0.1:8000/health
echo ==========================================================
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

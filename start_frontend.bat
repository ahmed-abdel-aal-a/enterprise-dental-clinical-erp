@echo off
chcp 65001 > nul
echo ==========================================================
echo [DentApex Enterprise] تشغيل خادم الواجهة الأمامية (Nuxt 4)...
echo ==========================================================
cd /d "%~dp0dentalpin-main\frontend"

if not exist "node_modules" (
    echo [خطأ] مجلد node_modules غير موجود! يرجى تشغيل npm install أولاً.
    pause
    exit /b 1
)

echo جاري تشغيل Nuxt Dev Server على المنفذ 3000...
echo الرابط المحلي: http://127.0.0.1:3000
echo ==========================================================
call npx nuxi dev --port 3000

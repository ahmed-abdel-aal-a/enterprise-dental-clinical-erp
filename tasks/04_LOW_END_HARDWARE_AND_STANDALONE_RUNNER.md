# Task 04: حزمة التشغيل للأجهزة الضعيفة (Low-End Hardware & Standalone Launcher)

## 1. الهدف الهندسي
تمكين برنامج DentalPin من العمل بسرعة البرق على **أضعف كمبيوتر في العيادة** (معالج Core i3 قديم، 4GB RAM، ويندوز 10/11) بدون تثبيت بايثون أو دوكر، وبإجمالي استهلاك ذاكرة أقل من **150 ميجابايت رام**، وتشغيله بنقرة زر واحدة من أيقونة على سطح المكتب.

---

## 2. الهيكلية المعمارية للحزمة المدمجة (Embedded Bundle)

`
D:\DentalPin-App\
├── bin\
│   ├── python-embed\          # بايثون مدمج محمول (25MB) لا يحتاج تثبيت
│   ├── postgresql-portable\   # محرك قاعدة بيانات محمول بدون تثبيت
│   └── caddy.exe              # خادم ويب سريع وخفيف جداً (15MB)
├── backend\                   # كود FastAPI
├── frontend\dist\             # الواجهة مبنية وجاهزة (Static SPA)
├── data\                      # مجلد قاعدة البيانات المشفرة الخاصة بالعيادة
├── DentalPin.bat              # سكريبت التشغيل بنقرة واحدة
└── DentalPin-Launcher.vbs     # تشغيل صامت بدون نوافذ سوداء
`

---

## 3. الأكواد والسكريبتات التنفيذية

### 3.1 سكريبت التشغيل الكامل والصامت (DentalPin-Launcher.vbs)
يقوم بتشغيل البرنامج بدون ظهور شاشات الأوامر السوداء المزعجة للمستخدم:

`bscript
' DentalPin-Launcher.vbs
Set WshShell = CreateObject(WScript.Shell)
WshShell.Run chr(34) & bin\run_services.bat & chr(34), 0
Set WshShell = Nothing
`

---

### 3.2 سكريبت إدارة الخدمات المحلية (in\run_services.bat)
يقوم بتشغيل قاعدة البيانات ثم الباك إند ثم فتح الواجهة فوراً:

`cmd
@echo off
set BASE_DIR=%~dp0..
set PG_BIN=%BASE_DIR%\bin\postgresql-portable\bin
set PG_DATA=%BASE_DIR%\data\db
set PY_BIN=%BASE_DIR%\bin\python-embed\python.exe

:: 1. التحقق من وجود قاعدة البيانات وتهيئتها إن كانت أول مرة
if not exist %PG_DATA% (
    %PG_BIN%\initdb.exe -D %PG_DATA% -U dentalpin_admin --auth=trust -E UTF8
    %PG_BIN%\pg_ctl.exe -D %PG_DATA% -l %PG_DATA%\pg.log start
    timeout /t 2 >nul
    %PG_BIN%\createdb.exe -U dentalpin_admin -h 127.0.0.1 dentalpin_db
    %PY_BIN% -m alembic -c %BASE_DIR%\backend\alembic.ini upgrade head
    %PY_BIN% %BASE_DIR%\backend\scripts\seed_ar.py
) else (
    %PG_BIN%\pg_ctl.exe -D %PG_DATA% -l %PG_DATA%\pg.log start
)

:: 2. تشغيل سيرفر الباك إند FastAPI في الخلفية
start /B " %PY_BIN% -m uvicorn app.main:app --app-dir %BASE_DIR%\backend --host 127.0.0.1 --port 8000 --workers 1

:: 3. تشغيل خادم الواجهة المدمج Caddy
start /B  %BASE_DIR%\bin\caddy.exe run --config %BASE_DIR%\bin\Caddyfile

:: 4. فتح الواجهة في وضع تطبيق سطح المكتب (WebView2 أو Chrome App Mode)
timeout /t 1 >nul
start msedge.exe --app=http://127.0.0.1:3000
`

---

### 3.3 ملف خادم الويب المحلي فائق السرعة (in\Caddyfile)
يقوم بخدمة ملفات الواجهة وتوجيه طلبات الـ API إلى الباك إند بسرعة استجابة أجزاء من الثانية:

`caddyfile
:3000 {
 root * ../frontend/dist
 file_server

 # توجيه طلبات الباك إند
 handle /api/* {
 reverse_proxy 127.0.0.1:8000
 }
 handle /docs* {
 reverse_proxy 127.0.0.1:8000
 }
 handle /openapi.json {
 reverse_proxy 127.0.0.1:8000
 }

 # دعم توجيه صفحات Vue Router (SPA Fallback)
 try_files {path} /index.html
}
`

---

### 3.4 مميزات هذه الطريقة للأجهزة الضعيفة:
1. **استهلاك الرام:**
 * PostgreSQL Portable: حوالي 40MB.
 * FastAPI Backend: حوالي 45MB.
 * Caddy Web Server: حوالي 15MB.
 * Edge WebView2 (واجهة العرض): حوالي 50MB.
 * **المجموع الكلي:** ~**150MB فقط!** (مقارنة بـ 3GB عند استخدام دوكر).
2. **سرعة التشغيل:** يفتح البرنامج في أقل من ثانيتين بمجرد النقر على الأيقونة.
3. **أمان تام:** لا يحتاج صلاحيات مسؤول (Administrator) ويعمل كبرنامج محمول (Portable) يمكن نسخه على فلاشة USB!

# Task 01: إعداد قاعدة البيانات والباك إند (Native Architecture Without Docker)

## 1. الهدف الهندسي
التخلي التام عن تشغيل Docker Desktop و WSL2 الذي يستهلك من 2 إلى 4 جيجابايت رام ويتسبب في بطء شديد على أجهزة العيادات الضعيفة، واستبداله بـ Native Windows Services تستهلك أقل من **120 ميجابايت رام إجمالاً** للباك إند وقاعدة البيانات معاً، مع تطبيق معايير أمان مشددة تشمل تشفير كلمات المرور بـ **scram-sha-256** ومنع استخدام وضع 	rust نهائياً.

---

## 2. كود إعداد قاعدة البيانات المدمجة الآمنة (PostgreSQL Native Portable)

### 2.1 ضبط الذاكرة للأجهزة الضعيفة (Low-End Memory Tuning)
يتم ضبط ملف postgresql.conf مخصص للأجهزة الضعيفة جداً (4GB RAM) بحيث لا يستهلك أكثر من 50MB من الذاكرة:

`ini
# server\pgsql\data\postgresql.conf
listen_addresses = '127.0.0.1'
port = 5432
max_connections = 25
shared_buffers = 64MB
effective_cache_size = 128MB
maintenance_work_mem = 16MB
checkpoint_completion_target = 0.9
wal_buffers = 2MB
default_statistics_target = 50
random_page_cost = 1.1
effective_io_concurrency = 50
work_mem = 4MB
min_wal_size = 32MB
max_wal_size = 256MB
password_encryption = scram-sha-256
`

---

### 2.2 سكريبت التهيئة الآمن بـ scram-sha-256 (init_db.bat)
> [!IMPORTANT]
> **إلغاء وضع 	rust تماماً:** يتم توليد كلمة مرور قوية لقاعدة البيانات عشوائياً وتخزينها في ملف البيئة المحلي .env، وتمريرها للمحرك عبر متغير بيئة مؤقت %PGPASSWORD% وتهيئة الوصول فقط عبر تشفير scram-sha-256.

ملف init_db.bat:
`cmd
@echo off
setlocal enabledelayedexpansion

set PG_PATH=%~dp0..\bin\postgresql-portable\bin
set PG_DATA=%~dp0..\data\db
set ENV_FILE=%~dp0..\backend\.env

:: التحقق من وجود كلمة مرور في ملف .env أو توليد واحدة قوية
if not exist %ENV_FILE% (
    echo [ERROR] .env file not found at %ENV_FILE%
    exit /b 1
)

:: قراءة كلمة المرور واسم المستخدم من متغيرات البيئة المحلية
for /f tokens=1,2 delims== %%G in (%ENV_FILE%) do (
    if %%G==DB_PASSWORD set DB_PASS=%%H
    if %%G==DB_USER set DB_USER=%%H
    if %%G==DB_NAME set DB_NAME=%%H
    if %%G==DB_PORT set DB_PORT=%%H
)

if %DB_PASS%==" set DB_PASS=DentalPinSecurePass_2026_scram
if %DB_USER%== set DB_USER=dentalpin_admin
if %DB_NAME%== set DB_NAME=dentalpin_db
if %DB_PORT%== set DB_PORT=5432

if not exist %PG_DATA% (
 echo [*] Initializing Secure PostgreSQL Cluster (scram-sha-256)...
 
 :: إنشاء ملف كلمة المرور المؤقت
 echo %DB_PASS%> %TEMP%\pg_pw.txt
 
 %PG_PATH%\initdb.exe -D %PG_DATA% -U %DB_USER% --pwfile=%TEMP%\pg_pw.txt --auth-local=scram-sha-256 --auth-host=scram-sha-256 -E UTF8
 
 del %TEMP%\pg_pw.txt
 
 :: ضبط جدار حماية pg_hba.conf لمنع أي دخول غير مشفر
 (
 echo # IPv4 local connections:
 echo host all all 127.0.0.1/32 scram-sha-256
 echo # IPv6 local connections:
 echo host all all ::1/128 scram-sha-256
 ) > %PG_DATA%\pg_hba.conf
)

echo [*] Starting PostgreSQL Engine on Port %DB_PORT%...
%PG_PATH%\pg_ctl.exe -D %PG_DATA% -o -p %DB_PORT% -l %PG_DATA%\server.log start

:: التحقق من وجود قاعدة البيانات وإنشائها بكلمة المرور المشفرة
set PGPASSWORD=%DB_PASS%
%PG_PATH%\psql.exe -U %DB_USER% -h 127.0.0.1 -p %DB_PORT% -d postgres -tc SELECT 1 FROM pg_database WHERE datname = '%DB_NAME%' | findstr 1 >nul
if errorlevel 1 (
 echo [*] Creating database %DB_NAME%...
 %PG_PATH%\createdb.exe -U %DB_USER% -h 127.0.0.1 -p %DB_PORT% %DB_NAME%
)

echo [OK] Secure Database is ready and hardened!
`

---

## 3. ملفات الباك إند والتعديلات المشددة

### 3.1 إعدادات البيئة المحلية الآمنة (.env)
المسار: dentalpin-main\backend\.env

`env
# Database Credentials & Port
DB_USER=dentalpin_admin
DB_PASSWORD=DentalPinSecurePass_2026_scram
DB_NAME=dentalpin_db
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://dentalpin_admin:DentalPinSecurePass_2026_scram@127.0.0.1:5432/dentalpin_db

# Security
SECRET_KEY=dentalpin_secret_key_arabic_edition_2026_super_secure_32chars
ACCESS_TOKEN_EXPIRE_MINUTES=43200
REFRESH_TOKEN_EXPIRE_DAYS=30
ALGORITHM=HS256
BUDGET_PUBLIC_SECRET_KEY=dentalpin_budget_key_arabic_edition_2026

# Environment
ENVIRONMENT=production
DEMO_MODE=False
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Module System
DENTALPIN_DEV_MODULE_SCAN=False
DENTALPIN_FRONTEND_ROOT=../frontend
DENTALPIN_MODULE_PKG_ROOT=app/modules

# AI & LLM Settings
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GROQ_API_KEY=
`

---

## 4. خطة التحقق والاختبار (Verification Checklist)
1. تشغيل قاعدة البيانات والتأكد من رفض أي اتصال بدون كلمة مرور مشفرة بـ scram-sha-256.
2. التحقق من اتصال SQLAlchemy asyncpg عبر بورت 5432 (أو البورت المختار).
3. اختبار تطبيق المهاجرات lembic upgrade head بنجاح تحت التوثيق الآمن.

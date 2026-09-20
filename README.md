<div align="center">

# 🦷 Enterprise Clinical Dental Practice Management & AI Copilot ERP
### *DentApex Enterprise - High-Performance Architecture for Dental Polyclinics*

[![Engineered by Apex Agency](https://img.shields.io/badge/Engineered_by-Apex_Agency-0ea5e9?style=for-the-badge&logo=google-chrome&logoColor=white)](https://apex-agency.tech)
[![Lead Architect](https://img.shields.io/badge/Architect-Eng._Ahmed_Abdel--Aal-10b981?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ahmed-abdel-aal-a)
[![Architecture Mode](https://img.shields.io/badge/Deployment-Enterprise_Full_Stack-f59e0b?style=for-the-badge)](https://apex-agency.tech)

---

<p align="center">
  <b>A mission-critical clinical management platform engineered for maximum uptime, cryptographic security, interactive odontogram charting, and generative AI diagnostic assistance.</b>
</p>

</div>

---

## 🌟 نظرة عامة (Overview)

نظام **DentApex Enterprise** هو الحل الشامل والمتقدم لإدارة مراكز وعيادات طب الأسنان، يجمع بين:
- **المخطط السني التفاعلي (Interactive Odontogram)**: دعم كامل للأسنان الدائمة واللبنية، الإجراءات السريرية، التشخيص، وتاريخ التعديلات الزمني.
- **محرك الحسابات والخزينة السريعة (Quick Cashier & Clinical Ledger)**: تسجيل الدفعات، توزيع الأرصدة على خطط العلاج والميزانيات، منع تعارض المعاملات (Row-level Locking) وسجل محاسبي مدقق.
- **مساعد الذكاء الاصطناعي السريري (Night Copilot)**: تكامل مع نماذج الذكاء الاصطناعي المحلية (Ollama / LLaMA 3.2) والسحابية (Groq / Gemini) لدعم اتخاذ القرار وتلخيص الحالات والبحث باللغة العربية.
- **تعدد الفروع والصلاحيات (Multi-Branch & Role-Based Access)**: إدارة فروع متعددة مع عزل البيانات وصلاحيات مخصصة لكل دور وظيفي.

---

## 🏗️ الهيكل المعماري (Architecture)

- **الواجهة الخلفية (Backend)**:
  - إطار العمل: `FastAPI` (Python 3.11)
  - قاعدة البيانات: `PostgreSQL` عبر `SQLAlchemy 2.0` (Async) و `Alembic`
  - الأمان والتحقق: `OAuth2 with JWT`, `Passlib/Bcrypt`
  - الخادم: `Uvicorn` على المنفذ `8000`

- **الواجهة الأمامية (Frontend)**:
  - إطار العمل: `Nuxt 4` / `Vue 3`
  - التصميم والمكونات: `@nuxt/ui`, `TailwindCSS`
  - التدويل: `@nuxtjs/i18n` مع دعم كامل للغة العربية و RTL
  - إدارة الحالة: `Pinia`
  - الخادم: `Nuxt Dev / Nitro` على المنفذ `3000`

---

## 🚀 التشغيل بنقرة واحدة (Quick Start)

تم تزويد هذا المستودع بملفات تشغيل تلقائية مخصصة لبيئة ويندوز:

1. **تشغيل النظام بالكامل (الباك إند + الفرونت إند + المتصفح)**:
   ```cmd
   run_all.bat
   ```
   *يقوم السكريبت تلقائياً بفحص وتنظيف المنافذ 8000 و 3000، تشغيل خادم FastAPI، تشغيل خادم Nuxt، ثم فتح المتصفح على `http://127.0.0.1:3000`.*

2. **تشغيل الباك إند فقط (Port 8000)**:
   ```cmd
   start_backend.bat
   ```

3. **تشغيل الواجهة الأمامية فقط (Port 3000)**:
   ```cmd
   start_frontend.bat
   ```

4. **إيقاف جميع الخوادم وتحرير المنافذ**:
   ```cmd
   stop_all.bat
   ```

---

## 🧪 فحص جاهزية النظام (Health Checks)

- **فحص صحة الخادم (Liveness)**:
  ```http
  GET http://127.0.0.1:8000/health
  Response: {"status": "healthy", "version": "2.0.0"}
  ```

- **فحص جاهزية قاعدة البيانات (Readiness)**:
  ```http
  GET http://127.0.0.1:8000/health/ready
  Response: {"status": "ready", "version": "2.0.0"}
  ```

---

## 📁 بنية المجلدات (Project Structure)

```text
dentapex-enterprise-original/
├── dentalpin-main/
│   ├── backend/               # خادم FastAPI، الموديولات، ونماذج قاعدة البيانات
│   │   ├── app/
│   │   │   ├── core/          # النواة: المصادقة، الفروع، نظام الملحقات
│   │   │   └── modules/       # موديولات النظام (28 موديول مستقل)
│   │   └── alembic/           # ملفات وترقيات قاعدة البيانات
│   ├── frontend/              # واجهة Nuxt 4 والمكونات السريرية
│   └── docs/                  # التوثيق الفني المعماري
├── tasks/                     # ملفات مهام التطوير المعماري والخطط
├── scripts/                   # سكريبتات مساعدة للنظام
├── run_all.bat                # مشغل النظام المتكامل
├── start_backend.bat          # مشغل الباك إند المستقل
├── start_frontend.bat         # مشغل الفرونت إند المستقل
└── stop_all.bat               # إيقاف الخوادم وتحرير المنافذ
```

---

## 🛡️ Security & Enterprise Regulatory Standards

- **Cryptographic Access Control:** Enforced `SCRAM-SHA-256` password hashing for all database access. Zero default `trust` authentication modes.
- **Zero Raw SQL Ingestion:** Strict asynchronous parameterized ORM mapping preventing all variants of SQL injection attacks (OWASP A03:2021).
- **Role-Based Access Control (RBAC):** Hierarchical permissions isolating Receptionists, Dental Hygienists, General Dentists, Specialized Surgeons, and Practice Financial Directors.
- **Multi-Branch Isolation:** Strict tenant separation ensuring individual clinic branches access only their authorized patient queues and billing ledgers.

---

## 📄 الترخيص (License)
جميع الحقوق محفوظة لمشروع DentApex Enterprise © 2026.

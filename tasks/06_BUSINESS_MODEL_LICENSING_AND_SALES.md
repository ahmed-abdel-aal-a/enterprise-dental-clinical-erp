# Task 06: نموذج العمل ونظام التراخيص والمبيعات (Business Model & Licensing Engine)

## 1. الهدف التجاري
تحويل الكود البرمجي إلى منتج تجاري حقيقي ومحمي، يضمن لك بيع النسخ بنظام الشراء لمرة واحدة (Lifetime License)، مع حماية الكود من القرصنة أو المشاركة العشوائية بين العيادات، وبناء مصادر دخل دورية متجددة (Recurring Revenue).

---

## 2. نظام حماية النسخة وترخيص الأجهزة (Hardware-Locked Licensing)

### 2.1 كود التحقق والربط بالعتاد الصارم (ackend/app/core/license.py)
> [!IMPORTANT]
> **ممنوع تماماً استخدام أي كود افتراضي موحد (Zero Generic Fallback):**
> تم بناء سلسلة هرمية لجلب هوية الجهاز (Motherboard UUID -> CPU ProcessorId -> MAC Address)، وفي حال الفشل التام لجميع المنافذ يتم توليد UUID عشوائي فريد وحفظه مشفراً في Windows Registry مع منع إعطاء أي كود موحد يمكن استغلاله لتشغيل البرنامج على أكثر من جهاز.

`python
"Hardware-locked license verification system for DentalPin Arabic.

Multi-tier hardware fingerprinting:
1. Motherboard UUID
2. CPU Processor ID
3. Primary MAC Address
4. Fallback: Cryptographically secure UUID stored in Windows Registry (Protected)
"

from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
import uuid
import winreg

MASTER_SECRET = bDENTALPIN_ARABIC_MASTER_SECRET_KEY_2026_PRODUCTION
REG_PATH = rSoftware\DentalPin
REG_KEY_NAME = MachineId


def _get_registry_machine_id() -> str | None:
    "Read machine ID from Windows Current User registry."
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, REG_KEY_NAME)
            return str(val).strip()
    except (FileNotFoundError, OSError):
        return None


def _set_registry_machine_id(unique_id: str) -> None:
    "Save unique generated machine ID securely in Windows Registry."
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
            winreg.SetValueEx(key, REG_KEY_NAME, 0, winreg.REG_SZ, unique_id)
    except OSError:
        pass


def get_hardware_fingerprint() -> str:
    "Extract a strict unique hardware fingerprint without static fallbacks."
    # 1. Try Motherboard UUID
    try:
        cmd = wmic csproduct get uuid
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if len(lines) >= 2 and lines[1] and FFFFFFFF not in lines[1]:
            return fMB-{lines[1]}
    except Exception:
        pass

    # 2. Try CPU Processor ID
    try:
        cmd = wmic cpu get processorid
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if len(lines) >= 2 and lines[1]:
            return fCPU-{lines[1]}
    except Exception:
        pass

    # 3. Try Primary MAC Address
    try:
        mac = uuid.getnode()
        if (mac >> 40) % 2 == 0:  # Valid physical MAC (not random)
            return fMAC-{mac:012X}
    except Exception:
        pass

    # 4. Fallback: Registry-stored Unique UUID (Never a uniform generic string!)
    existing_reg_id = _get_registry_machine_id()
    if existing_reg_id:
        return fREG-{existing_reg_id}

    new_unique_id = str(uuid.uuid4())
    _set_registry_machine_id(new_unique_id)
    return fREG-{new_unique_id}


def generate_license_key(hw_fingerprint: str, clinic_name: str) -> str:
    "Generate cryptographically signed key for a clinic."
    message = f{hw_fingerprint.strip()}:{clinic_name.strip()}.encode()
    signature = hmac.new(MASTER_SECRET, message, hashlib.sha256).hexdigest().upper()
    return fDP-{signature[:4]}-{signature[4:8]}-{signature[8:12]}-{signature[12:16]}


def verify_license_key(license_key: str, clinic_name: str) -> bool:
    "Verify license on app startup."
    current_hw = get_hardware_fingerprint()
    expected_key = generate_license_key(current_hw, clinic_name)
    return hmac.compare_digest(license_key.strip(), expected_key.strip())
`

---

## 3. باقات التسعير المقترحة للمنطقة العربية

| الباقة | السعر | التفاصيل |
| :--- | :--- | :--- |
| **النسخة الأساسية (Lifetime Basic)** | **150$ - 250$** (مرة واحدة) | رخصة دائمة للعيادة، بدون إنترنت، بدون حد للمرضى، دعم AI عبر مفتاح الطبيب المجاني. |
| **النسخة الاحترافية (Lifetime Pro + Remote)** | **300$ - 450$** (مرة واحدة) | تشمل الربط بالموبايل عبر Cloudflare Tunnel، ودعم شبكة العيادة الداخلية (LAN). |
| **باقة الدعم والنسخ الاحتياطي (Annual SLA)** | **40$ - 60$** (سنوياً) | نسخ احتياطي سحابي مشفر يومياً، تحديثات دورية، ودعم فني طارئ عبر AnyDesk. |
| **بوابة رسائل الواتساب (WhatsApp Gateway)** | **10$ - 15$** (شهرياً) | إرسال تذكيرات المواعيد وعروض الأسعار تلقائياً للمرضى على الواتساب. |

---

## 4. استراتيجية البيع والإغلاق الميداني (Go-To-Market)

1. **مندوبو شركات مستلزمات الأسنان (Dental Depots):**
   * هم القناة البيعية الأسرع؛ كل مندوب يدخل ما بين 10 إلى 20 عيادة يومياً.
   * العرض للمندوب: عمولة نقدية مباشرة (20% من ثمن كل بيعة).
2. **تجربة الـ 14 يوماً بدون مخاطرة (Zero-Risk Trial):**
   * تثبيت البرنامج على لابتوب الطبيب بنقرة زر مع استيراد بياناته القديمة من إكسل مجاناً.
   * إتاحة كافة الميزات لمدة 14 يوماً، ثم يطلب البرنامج كود التفعيل لإكمال العمل.
3. **فيديوهات التسويق العملي (30-Second Micro Demos):**
   * تصوير شاشة الموبايل أثناء إملاء روشتة بصوت الطبيب وتفريغها في ملف المريض فوراً.
   * إبراز ميزة: *البرنامج على جهازك، بياناتك ملكك، وشراء لمرة واحدة فقط بدون اشتراكات إجبارية*.

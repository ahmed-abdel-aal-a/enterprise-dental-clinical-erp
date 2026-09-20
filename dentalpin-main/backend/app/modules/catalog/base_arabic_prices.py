"""Baseline pricing template for Arabic dental clinics (Multi-tenant isolated).

Provides realistic default prices in local currency (EGP/SAR/AED/USD) for all 129
dental catalog procedures, plus default flags (is_default_for_type) for odontogram types.
Each clinic (tenant) receives its own cloned prices and edits them independently.
"""

from decimal import Decimal
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import TreatmentCatalogItem, TreatmentOdontogramMapping

# Default catalog codes for primary Odontogram clinical types
DEFAULT_CLINICAL_TYPE_CODES: dict[str, str] = {
    "filling_composite": "REST-COMP",           # حشو كمبوزيت ضوئي (تجميلي)
    "crown": "REST-CROWN-ZIR",                   # تاج زيركون كامل (Full Zirconia)
    "root_canal_full": "ENDO-MULTI",             # علاج عصب ضرس متعدد القنوات (طاحن)
    "extraction": "SURG-EXT-SIMPLE",             # خلع سن بسيط
    "implant": "SURG-IMP-TI",                    # زراعة سن تيتانيوم
    "veneer": "REST-VEN-COMP",                   # قشرة كمبوزيت تجميلية
    "bridge": "REST-BRIDGE-ZIR",                 # جسر زيركون تجميلي
    "inlay": "REST-INLAY-COMP",                  # حشوة مصبوبة إنلاي
    "overlay": "REST-OVER-COMP",                 # حشوة مصبوبة أوفرلاي
    "sealant": "PREV-SEAL",                      # سد الشقوق والميازيب
    "splint": "REST-SPLINT-OCC",                 # جبيرة إطباقية
    "apicoectomy": "SURG-APEC",                  # استئصال قمة الجذر
    "bracket": "ORTO-METAL",                     # حاصرات تقويمية معدنية
    "retainer": "ORTO-RET-FIX",                  # مثبت تقويمي ثابت
    "filling_temporary": "REST-TEMP",            # حشو مؤقت
    "provisional_crown": "REST-CROWN-PROV",      # تاج مؤقت
}

# Baseline realistic clinic prices in local currency (EGP) for all 129 procedures
BASE_ARABIC_CATALOG_PRICES: dict[str, Decimal] = {
    # 1. التشخيص والأشعة (Diagnostics & Radiology - DX)
    "DX-VISIT": Decimal("200.00"),           # كشف أولي وفحص وتشخيص
    "DX-REVIEW": Decimal("100.00"),          # كشف دوري ومتابعة
    "DX-URGENT": Decimal("250.00"),          # كشف طوارئ وألم حاد
    "DX-2ND-OPINION": Decimal("250.00"),     # استشارة طبية ثانية
    "DX-RXPA": Decimal("100.00"),            # أشعة سينية حول ذروية
    "DX-RXPAN": Decimal("250.00"),           # أشعة بانورامية للفكين
    "DX-CBCT": Decimal("700.00"),            # أشعة مقطعية ثلاثية الأبعاد (CBCT)
    "DX-TELE": Decimal("250.00"),            # أشعة سيفالومترية جانبية
    "DX-PHOTO": Decimal("150.00"),           # تصوير فوتوغرافي داخل الفم
    "DX-STUDY": Decimal("300.00"),           # دراسة تقويمية للحالة

    # 2. علاج الجذور والعصب (Endodontics - ENDO)
    "ENDO-UNI": Decimal("1000.00"),          # علاج عصب سن أحادي القناة (أمامي)
    "ENDO-BI": Decimal("1200.00"),           # علاج عصب سن ثنائي القنوات (ضاحك)
    "ENDO-MULTI": Decimal("1500.00"),        # علاج عصب ضرس متعدد القنوات (طاحن)
    "ENDO-RETREAT": Decimal("1800.00"),      # إعادة علاج عصب وقنوات الجذور
    "ENDO-URGENT": Decimal("400.00"),        # فتح حجرة اللب وتسكين الألم كطوارئ
    "ENDO-APICOFORM": Decimal("800.00"),     # علاج قمة الجذر غير المكتملة
    "ENDO-PED": Decimal("500.00"),           # علاج عصب سن لبني للأطفال
    "ENDO-MED-REFRESH": Decimal("200.00"),   # تبديل الضماد الدوائي داخل القناة
    "ENDO-POST-FIBER": Decimal("600.00"),    # وتد فايبر داخل القناة
    "ENDO-POST-METAL": Decimal("500.00"),    # وتد معدني مصبوب

    # 3. العلاج الترميمي والحشوات (Restorative - REST)
    "REST-COMP": Decimal("600.00"),          # حشو كمبوزيت ضوئي (تجميلي)
    "REST-RECONSTR": Decimal("800.00"),      # بناء وإعادة هيكلة السن بالكمبوزيت
    "REST-FILL-REPAIR": Decimal("350.00"),   # إصلاح وتعديل الحشوة
    "REST-TEMP": Decimal("150.00"),          # حشو مؤقت
    "REST-AMAL": Decimal("400.00"),          # حشو أملغم فضي
    "REST-CROWN-MC": Decimal("1200.00"),     # تاج معدن-بورسلين (PFM)
    "REST-CROWN-ZIR": Decimal("2200.00"),    # تاج زيركون كامل (Full Zirconia)
    "REST-CROWN-DISI": Decimal("2800.00"),   # تاج إيماكس (E-max)
    "REST-CROWN-METAL": Decimal("800.00"),   # تاج معدني مصبوب كامل
    "REST-CROWN-PROV": Decimal("300.00"),    # تاج مؤقت
    "REST-CROWN-RECEMENT": Decimal("200.00"),# إعادة تثبيت ولصق التاج
    "REST-CROWN-POST-ENDO": Decimal("1400.00"), # تاج فوق سن معالج عصبه
    "REST-CROWN-IMPL-MC": Decimal("3000.00"),# تاج معدن-بورسلين فوق زرعة
    "REST-CROWN-IMPL-ZIR": Decimal("4000.00"),# تاج زيركون فوق زرعة
    "REST-CROWN-IMPL-PROV": Decimal("800.00"),# تاج مؤقت فوق زرعة
    "REST-BRIDGE-MC": Decimal("3600.00"),    # جسر معدن-بورسلين (3 وحدات)
    "REST-BRIDGE-ZIR": Decimal("6600.00"),   # جسر زيركون كامل (3 وحدات)
    "REST-BRIDGE-MARY": Decimal("2000.00"),  # جسر ماريلاند
    "REST-INLAY-COMP": Decimal("900.00"),    # إنلاي كمبوزيت غير مباشر
    "REST-INLAY-CER": Decimal("1500.00"),    # إنلاي خزفي تجميلي
    "REST-OVER-COMP": Decimal("1100.00"),    # أوفرلاي كمبوزيت
    "REST-OVER-CER": Decimal("1800.00"),     # أوفرلاي خزفي
    "REST-VEN-COMP": Decimal("1200.00"),     # قشرة تجميلية كمبوزيت
    "REST-VEN-PORC": Decimal("2500.00"),     # قشرة خزفية (فينير بورسلين)
    "REST-VEN-ZIR": Decimal("2800.00"),      # قشرة فينير زيركون
    "REST-DEF-ABUT": Decimal("1500.00"),     # دعامة زرعة نهائية
    "REST-HEAL-ABUT": Decimal("500.00"),     # دعامة التئام زرعة
    "REST-SPLINT-OCC": Decimal("1000.00"),   # جبيرة إطباقية واقية
    "REST-SPLINT-PERIO": Decimal("800.00"),  # جبيرة لتثبيت الأسنان المخلخلة

    # 4. جراحة الفم وزراعة الأسنان (Surgery & Implants - SURG)
    "SURG-EXT-SIMPLE": Decimal("350.00"),    # خلع سن بسيط
    "SURG-EXT-COMPLEX": Decimal("600.00"),   # خلع سن معقد
    "SURG-EXT-OST": Decimal("1000.00"),      # خلع جراحي مع قص عظمي
    "SURG-EXT-3MOLAR": Decimal("1500.00"),   # خلع ضرس العقل
    "SURG-EXT-INCLUIDO": Decimal("2000.00"), # خلع سن مطمور بالكامل
    "SURG-APEC": Decimal("1500.00"),         # استئصال ذروة الجذر (Apicoectomy)
    "SURG-IMP-TI": Decimal("9000.00"),       # زراعة سن تيتانيوم
    "SURG-IMP-ZIR": Decimal("12000.00"),     # زراعة سن زيركون
    "SURG-SINUS": Decimal("6000.00"),        # رفع الجيب الفكي جراحياً
    "SURG-SINUS-CLOSED": Decimal("3500.00"), # رفع الجيب الفكي المغلق
    "SURG-BONE-GRAFT": Decimal("2500.00"),   # طعم عظمي تعويضي
    "SURG-BONE-HORIZ": Decimal("3000.00"),   # توسيع عظمي أفقي
    "SURG-BONE-VERT": Decimal("3500.00"),    # تكبير عظمي عمودي
    "SURG-BONE-REGUL": Decimal("800.00"),    # تسوية وتعديل الحافة العظمية
    "SURG-CONN-GRAFT": Decimal("2000.00"),   # طعم نسيج ضام لثوي
    "SURG-CROWN-LENGTH": Decimal("1000.00"), # تطويل التاج السريري
    "SURG-FREN": Decimal("800.00"),          # قطع لجام الشفة أو اللسان
    "SURG-CYST": Decimal("1500.00"),         # استئصال كيس فكي
    "SURG-BIOPSY": Decimal("600.00"),        # أخذ خزعة نسيجية
    "SURG-PRP": Decimal("1000.00"),          # حقن البلازما الغنية بالصفائح (PRP)
    "SURG-PERIIMP": Decimal("1200.00"),      # علاج التهاب الأنسجة حول الزرعة

    # 5. علاج اللثة والوقاية (Periodontics & Prevention - PERIO & PREV)
    "PREV-CLEAN": Decimal("500.00"),         # تنظيف وتلميع الأسنان وإزالة الجير
    "PREV-CHECKUP": Decimal("200.00"),       # فحص وقائي شامل
    "PREV-FLUOR": Decimal("300.00"),         # تطبيق فلورايد موضعي
    "PREV-SEAL": Decimal("250.00"),          # سد الشقوق السنية (للضرس)
    "PREV-CLEAN-PED": Decimal("350.00"),     # تنظيف وتلميع أسنان أطفال
    "PREV-HYGIENE-EDU": Decimal("100.00"),   # جلسة توعية بالصحة الفموية
    "PREV-CLEAN-CURETTAGE": Decimal("800.00"), # تنظيف عميق مع كشط اللثة
    "PERIO-SCAL": Decimal("600.00"),         # تقليح فوق وتحت اللثة
    "PERIO-RAR": Decimal("800.00"),          # تجريف جذور عميق لكل ربع فك
    "PERIO-CURET-SEXT": Decimal("400.00"),   # كشط لثوي لسدس فك
    "PERIO-MAINT": Decimal("400.00"),        # جلسة صيانة دورية للثة
    "PERIO-STUDY": Decimal("400.00"),        # دراسة ومخطط لثوي كامل
    "PERIO-GINGIV": Decimal("1000.00"),      # قص وتجميل اللثة (Gingivectomy)
    "PERIO-GRAFT": Decimal("2500.00"),       # طعم لثوي حر
    "PERIO-BONE": Decimal("2000.00"),        # جراحة عظمية تجديدية للثة
    "PERIO-SURG": Decimal("1200.00"),        # جراحة شريحة لثوية
    "PERIO-SURG-REGEN": Decimal("2800.00"),  # جراحة لثوية تجديدية
    "PERIO-SURG-RESECT": Decimal("1500.00"), # جراحة لثوية استئصالية
    "PERIO-SPLINT-RAR": Decimal("1000.00"),  # تثبيت لثوي مع كحت الجذور

    # 6. طب أسنان الأطفال (Pediatric - PED)
    "PED-FILL-TEMP": Decimal("350.00"),      # حشو سن لبني للأطفال
    "PED-PULPOTOMY": Decimal("500.00"),      # بتر الحجرة اللبية (Pulpotomy)
    "PED-PULPECTOMY": Decimal("600.00"),     # استئصال اللب الكامل لسن لبني
    "PED-CROWN-SS": Decimal("700.00"),       # تاج ستانلس ستيل للأطفال (SSC)
    "PED-EXT-TEMP": Decimal("250.00"),       # خلع سن لبني للأطفال
    "PED-SPACE": Decimal("1200.00"),         # حافظ مسافة وحيد الجانب
    "PED-SPACE-COMPOUND": Decimal("1800.00"),# حافظ مسافة ثنائي الجانب
    "PED-SEAL": Decimal("250.00"),           # سد ميازيب أطفال
    "PED-FLUOR": Decimal("300.00"),          # جلسة فلورايد أطفال

    # 7. الاستعاضة الصناعية والتركيبات المتحركة (Prosthetics - PROT)
    "PROT-FULL-SUP": Decimal("5000.00"),     # طقم أسنان كامل للفك العلوي
    "PROT-FULL-INF": Decimal("5000.00"),     # طقم أسنان كامل للفك السفلي
    "PROT-PART-ACR": Decimal("2500.00"),     # طقم أسنان جزئي أكريلي
    "PROT-PART-METAL": Decimal("4000.00"),   # طقم أسنان جزئي هيكل معدني (كوبلت كروم)
    "PROT-OVERDENT": Decimal("7000.00"),     # طقم فوق الزرعات (Overdenture)
    "PROT-PROV-REMOV": Decimal("1000.00"),   # طقم متحرك مؤقت
    "PROT-REPAIR": Decimal("400.00"),        # تصليح كسر طقم أسنان
    "PROT-REBASE": Decimal("800.00"),        # تبطين وتجديد قاعدة الطقم (Rebase)
    "PROT-OCC-ADJ": Decimal("200.00"),       # تعديل الإطباق وإزالة نقاط الضغط

    # 8. طب الأسنان التجميلي وتبييض الأسنان (Aesthetics - EST)
    "EST-BLAN-CLIN": Decimal("2500.00"),     # تبييض أسنان احترافي بالعيادة
    "EST-BLAN-AMB": Decimal("1500.00"),      # تبييض أسنان منزلي مع القوالب
    "EST-BLAN-COMBO": Decimal("3200.00"),    # تبييض مشترك (عيادة + منزلي)
    "EST-COMP-AESTH": Decimal("1200.00"),    # حشو كمبوزيت تجميلي متعدد الطبقات
    "EST-MICROAB": Decimal("800.00"),        # معالجة تصبغات المينا الدقيقة
    "EST-PIG-REMOVE": Decimal("600.00"),     # إزالة تصبغات اللثة بالليزر/جراحياً
    "EST-REMIN": Decimal("300.00"),          # إعادة تمعدن المينا بالمعاجين الخاصة

    # 9. تقويم الأسنان (Orthodontics - ORTO)
    "ORTO-METAL": Decimal("18000.00"),       # علاج تقويم كامل - حاصرات معدنية
    "ORTO-CERAM": Decimal("24000.00"),       # علاج تقويم كامل - حاصرات شفافة خزفية
    "ORTO-LINGUAL": Decimal("35000.00"),     # علاج تقويم لساني خلفي
    "ORTO-INV-FULL": Decimal("38000.00"),    # تقويم شفاف كامل (Aligners)
    "ORTO-INV-LITE": Decimal("22000.00"),    # تقويم شفاف خفيف
    "ORTO-REVIEW": Decimal("300.00"),        # جلسة شد ومتابعة تقويم شهري
    "ORTO-RET-FIX": Decimal("800.00"),       # مثبت تقويم سلكي ثابت لكل فك
    "ORTO-RET-REM": Decimal("600.00"),       # مثبت تقويم متحرك شفاف (Essix)
    "ORTO-BRACK": Decimal("200.00"),         # إعادة لصق حاصرة تقويمية ساقطة
    "ORTO-BRACK-CEMENT": Decimal("150.00"),  # تثبيت طوق تقويمي
    "ORTO-BRACK-DEBOND": Decimal("1000.00"), # فك وإزالة أجهزة التقويم وتلميع المينا
    "ORTO-PALATAL-EXP": Decimal("3500.00"),  # جهاز توسيع الفك العلوي
    "ORTO-TAD": Decimal("1500.00"),          # زرعة تقويمية صغيرة (Mini-screw)
    "ORTO-ATTACH": Decimal("300.00"),        # وضع وصلات تقويمية مخصصة
    "ORTO-SEPARATOR": Decimal("100.00"),     # وضع فواصل مطاطية بين الأسنان
}


async def apply_baseline_prices_for_clinic(db: AsyncSession, clinic_id: UUID) -> dict[str, int]:
    """Populate baseline prices and set is_default_for_type for a specific clinic.
    
    Multi-tenant isolation: strictly filters by clinic_id. Does not affect other clinics.
    """
    # 1. Update prices for the clinic's items based on baseline template
    updated_prices = 0
    for code, price in BASE_ARABIC_CATALOG_PRICES.items():
        stmt = (
            update(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.internal_code == code,
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .values(default_price=price)
        )
        res = await db.execute(stmt)
        updated_prices += res.rowcount

    # 2. Reset and mark is_default_for_type for mapped items
    await db.execute(
        update(TreatmentCatalogItem)
        .where(TreatmentCatalogItem.clinic_id == clinic_id)
        .values(is_default_for_type=False)
    )

    default_flags_set = 0
    for odontogram_type, default_code in DEFAULT_CLINICAL_TYPE_CODES.items():
        stmt = (
            update(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.internal_code == default_code,
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .values(is_default_for_type=True)
        )
        res = await db.execute(stmt)
        default_flags_set += res.rowcount

    await db.flush()
    return {"updated_prices": updated_prices, "default_flags_set": default_flags_set}

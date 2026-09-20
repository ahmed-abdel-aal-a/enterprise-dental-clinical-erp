# Task 02: التعريب الكامل ودعم الاتجاه من اليمين لليسار (Arabic Localization & RTL Architecture)

## 1. الهدف الهندسي
تحويل واجهة DentalPin إلى نظام عربي متكامل وسلس، مع حل المعضلة السريرية في **مخطط الأسنان (Odontogram)** لضمان عدم انعكاس ترتيب الأسنان طبياً، وتوفير خطوط عربية محلية (Offline Fonts) تعمل بدون اتصال بالإنترنت، وتعريب تقارير وفواتير الـ PDF.

---

## 2. الأكواد الدقيقة التي سيتم تعديلها وإضافتها

### 2.1 تسجيل اللغة العربية في rontend/nuxt.config.ts
المسار: rontend/nuxt.config.ts
الحالة الحالية: ملف r.json موجود ولكن غير مسجل في مصفوفة اللغات.
التعديل المطلوب في قسم i18n:

`	ypescript
// frontend/nuxt.config.ts
i18n: {
  locales: [
    { code: 'ar', name: 'العربية', file: 'ar.json', dir: 'rtl' },
    { code: 'en', name: 'English', file: 'en.json', dir: 'ltr' },
    { code: 'es', name: 'Español', file: 'es.json', dir: 'ltr' }
  ],
  defaultLocale: 'ar',
  lazy: true,
  langDir: 'locales',
  strategy: 'no_prefix',
  detectBrowserLanguage: {
    useCookie: true,
    cookieKey: 'dentalpin_locale',
    fallbackLocale: 'ar'
  }
}
`

---

### 2.2 تفعيل سمة الـ RTL الديناميكية في rontend/app/app.vue
المسار: rontend/app/app.vue
التعديل في useHead واستيراد لغة Nuxt UI:

`ue
<!-- frontend/app/app.vue -->
<script setup lang=ts>
import { fr, es, en, pt, de, hu, pl, it, ar } from '@nuxt/ui/locale'

const { t, locale } = useI18n()

// دعم لغة الواجهة العربية لمكونات Nuxt UI
const nuxtUILocales: Record<string, any> = { ar, en, fr, es, pt, de, hu, pl, it }
const nuxtUILocale = computed(() => nuxtUILocales[locale.value] || ar)

useHead(() => ({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: locale.value,
    dir: locale.value === 'ar' ? 'rtl' : 'ltr'
  }
}))

useSeoMeta({
  title: 'DentalPin - النسخة العربية الذكية',
  description: t('app.tagline')
})
</script>
`

---

### 2.3 حماية مخطط الأسنان (Odontogram) من الانعكاس الخاطئ
**الأهمية السريرية:** ترقيم الأسنان العالمي (FDI Notation) يعتمد على:
* الربع الأول (Upper Right: 18 - 11) يظهر على **يسار الشاشة** للمشاهد (يمين المريض).
* الربع الثاني (Upper Left: 21 - 28) يظهر على **يمين الشاشة** للمشاهد (يسار المريض).

إذا تُركت الحاوية لقواعد RTL العامة، ستنعكس الأسنان بصرياً مما يؤدي إلى علاج السن الخطأ!
المسار: ackend/app/modules/odontogram/frontend/components/odontogram/OdontogramChart.vue
التعديل: عزل شبكة الأسنان بـ dir=ltr صريح:

`ue
<!-- داخل OdontogramChart.vue -->
<div class=odontogram-wrapper>
  <!-- فرض الاتجاه الطبي الدولي الثابت للأسنان -->
  <div
    class=odontogram-grid bg-surface rounded-lg border border-default p-4
    dir=ltr
    :class={ 'cursor-crosshair': isClickToApplyMode }
  >
    <!-- Upper arch -->
    <div class=mb-6 arch-container :class={ 'arch-halo': hoveredArch === 'upper' }>
      <div class=text-caption text-subtle text-center mb-2 dir=rtl>
        {{ t('odontogram.quadrants.upper') }}
      </div>
      <div class=flex justify-center gap-1 relative>
        <ToothQuadrant :teeth=teethLayout.upperRight ... />
        <ToothQuadrant :teeth=teethLayout.upperLeft ... />
      </div>
    </div>
    ...
`

---

### 2.4 ملف ترجمة الذكاء الاصطناعي الناقص
المسار: ackend/app/modules/copilot/frontend/i18n/locales/ar.json
تم اكتشاف عدم وجود ملف عربي لوحدة الذكاء الاصطناعي (Copilot). يتم إنشاء الملف ليشمل:
* رسائل التأكيد قبل اتخاذ القرارات السريرية (confirmations).
* التلميحات الذكية لملء الفراغات في الجدول (illGaps).
* ملخص الحالة الصباحي للعيادة (dailyBriefing).

---

### 2.5 دعم الخط العربي المحلي بدون اتصال بالإنترنت (Offline Cairo Font)
المسار: rontend/app/assets/css/main.css
تضمين خط Cairo بصيغة woff2 محلياً داخل مجلد ssets/fonts:

`css
@font-face {
  font-family: 'Cairo';
  src: url('/fonts/Cairo-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Cairo';
  src: url('/fonts/Cairo-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

body, html, [dir=rtl] {
  font-family: 'Cairo', system-ui, -apple-system, sans-serif;
}
`

---

### 2.6 تعريب فواتير وروشتات الـ PDF (WeasyPrint Engine)
المسارات:
* ackend/app/modules/billing/templates/invoice.html
* ackend/app/modules/budget/templates/budget.html

إضافة تنسيق CSS لدعم اتجاه RTL والخط العربي في قوالب الطباعة:
`html
<style>
  @page {
    size: A4;
    margin: 1.5cm;
  }
  body {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', sans-serif;
  }
  .invoice-table th, .invoice-table td {
    text-align: right;
  }
</style>
`

<template>
  <div>
    <!-- Top License Notice Banner (Only shown during Trial, Expired, or Tampered states) -->
    <div
      v-if="status && status !== 'licensed'"
      class="w-full px-4 py-2 text-xs flex items-center justify-between transition-all border-b"
      :class="bannerClasses"
      dir="rtl"
    >
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span
            class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
            :class="status === 'trial' ? 'bg-amber-400' : 'bg-red-400'"
          ></span>
          <span
            class="relative inline-flex rounded-full h-2 w-2"
            :class="status === 'trial' ? 'bg-amber-500' : 'bg-red-500'"
          ></span>
        </span>

        <span class="font-medium">
          <template v-if="status === 'trial'">
            ⏳ فترة تجريبية مجانية: متبقي {{ daysLeft }} يوم على انتهاء التجربة
          </template>
          <template v-else-if="status === 'expired'">
            ⚠️ انتهت فترة التجربة المجانية (14 يوماً) — العمليات مقفلة حتى إدخال كود التفعيل
          </template>
          <template v-else-if="status === 'tampered'">
            🚫 تم كشف تلاعب في ساعة النظام أو السجل الزمني — البرنامج متوقف للحماية
          </template>
        </span>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="showModal = true"
          class="px-3 py-1 font-semibold rounded text-xs transition shadow-xs"
          :class="buttonClasses"
        >
          🔑 تفعيل النسخة الدائمة
        </button>
      </div>
    </div>

    <!-- Activation Modal -->
    <div
      v-if="showModal || status === 'expired' || status === 'tampered'"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
      dir="rtl"
    >
      <div class="bg-surface rounded-token-xl border border-subtle max-w-md w-full p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-subtle pb-3">
          <div class="flex items-center gap-2">
            <span class="text-xl">🛡️</span>
            <h3 class="text-base font-bold text-default">تفعيل رخصة DentApex الرسمية</h3>
          </div>
          <button
            v-if="status === 'trial'"
            type="button"
            @click="showModal = false"
            class="text-muted hover:text-default text-lg leading-none"
          >
            ✕
          </button>
        </div>

        <p class="text-xs text-muted leading-relaxed">
          نظام DentApex يعمل بترخيص دائم مدى الحياة مربوط بعتاد جهاز العيادة (Hardware-Locked).
          انسخ بصمة جهازك أدناه وأرسلها للمطور لتوليد مفتاح التفعيل الرسمي لعيادتك.
        </p>

        <!-- Hardware Fingerprint Box -->
        <div class="bg-surface-muted border border-subtle rounded-token-md p-3 space-y-1">
          <span class="text-[11px] font-medium text-muted block">بصمة عتاد هذا الجهاز (Hardware ID):</span>
          <div class="flex items-center justify-between gap-2">
            <code class="font-mono text-sm font-bold text-primary tracking-wider">{{ hwFingerprint }}</code>
            <button
              type="button"
              @click="copyHwId"
              class="px-2.5 py-1 bg-surface border border-subtle hover:bg-surface-muted text-default text-xs rounded transition flex items-center gap-1"
            >
              <span>{{ copied ? 'تم النسخ ✓' : 'نسخ' }}</span>
            </button>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="submitActivation" class="space-y-3">
          <div>
            <label class="block text-xs font-semibold text-default mb-1">اسم العيادة (كما تم ترخيصه):</label>
            <input
              v-model="formClinicName"
              type="text"
              required
              placeholder="مثال: عيادة النور لطب الأسنان"
              class="w-full px-3 py-2 bg-canvas border border-subtle rounded-token-md text-sm text-default focus:border-primary focus:outline-hidden"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-default mb-1">كود الترخيص (License Key):</label>
            <input
              v-model="formLicenseKey"
              type="text"
              required
              placeholder="DP-XXXX-XXXX-XXXX-XXXX"
              class="w-full px-3 py-2 bg-canvas border border-subtle rounded-token-md text-sm font-mono text-default tracking-wider uppercase focus:border-primary focus:outline-hidden"
            />
          </div>

          <div v-if="errorMessage" class="p-2.5 rounded bg-red-500/10 border border-red-500/20 text-red-600 text-xs">
            {{ errorMessage }}
          </div>

          <div v-if="successMessage" class="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 text-xs font-semibold">
            {{ successMessage }}
          </div>

          <div class="pt-2 flex items-center justify-end gap-2">
            <button
              v-if="status === 'trial'"
              type="button"
              @click="showModal = false"
              class="px-3 py-2 text-xs text-muted hover:text-default rounded transition"
            >
              إغلاق
            </button>
            <button
              type="submit"
              :disabled="loading"
              class="px-4 py-2 bg-primary hover:bg-primary/90 text-white text-xs font-bold rounded-token-md shadow-xs transition disabled:opacity-50"
            >
              {{ loading ? 'جاري التحقق...' : 'تفعيل الرخصة الآن' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const status = ref<string | null>(null)
const daysLeft = ref<number | null>(null)
const hwFingerprint = ref<string>('')
const showModal = ref(false)
const copied = ref(false)

const formClinicName = ref('')
const formLicenseKey = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const bannerClasses = computed(() => {
  if (status.value === 'trial') {
    return 'bg-amber-500/10 border-amber-500/20 text-amber-900 dark:text-amber-200'
  }
  return 'bg-red-500/15 border-red-500/30 text-red-900 dark:text-red-200'
})

const buttonClasses = computed(() => {
  if (status.value === 'trial') {
    return 'bg-amber-500 hover:bg-amber-600 text-white'
  }
  return 'bg-red-600 hover:bg-red-700 text-white'
})

async function fetchStatus() {
  try {
    const res = await $fetch<any>('/api/v1/license/status')
    status.value = res.status
    daysLeft.value = res.days_left
    hwFingerprint.value = res.hw_fingerprint
    if (res.clinic_name && !formClinicName.value) {
      formClinicName.value = res.clinic_name
    }
  } catch (err) {
    // Ignore network errors in offline/boot phase
  }
}

async function copyHwId() {
  if (!hwFingerprint.value) return
  try {
    await navigator.clipboard.writeText(hwFingerprint.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2500)
  } catch {
    // Clipboard permission fallback
  }
}

async function submitActivation() {
  errorMessage.value = ''
  successMessage.value = ''
  loading.value = true

  try {
    const res = await $fetch<any>('/api/v1/license/activate', {
      method: 'POST',
      body: {
        license_key: formLicenseKey.value.trim().toUpperCase(),
        clinic_name: formClinicName.value.trim(),
      },
    })

    if (res.success) {
      successMessage.value = 'تم تفعيل رخصة DentApex الدائمة بنجاح! 🎉'
      status.value = 'licensed'
      setTimeout(() => {
        showModal.value = false
        window.location.reload()
      }, 1500)
    }
  } catch (err: any) {
    errorMessage.value = err.data?.detail || 'فشل التفعيل: يرجى التأكد من صحة كود الترخيص واسم العيادة.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStatus()
})
</script>

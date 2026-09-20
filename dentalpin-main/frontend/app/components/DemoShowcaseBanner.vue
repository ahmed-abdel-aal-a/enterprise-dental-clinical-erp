<template>
  <div v-if="isVisible" dir="rtl" class="relative z-40">
    <!-- Top Showcase Banner Bar -->
    <div
      class="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 text-white shadow-md border-b border-emerald-500/30"
    >
      <div class="max-w-7xl mx-auto px-3 sm:px-4 py-2 flex flex-wrap items-center justify-between gap-2 text-xs sm:text-sm">
        <!-- Left info section (Arabic RTL: starts from right) -->
        <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-white/20 text-white shadow-xs backdrop-blur-xs">
            <span class="h-2 w-2 rounded-full bg-emerald-300 animate-pulse"></span>
            معاينة حية تفاعلية
          </span>

          <span class="font-medium text-emerald-50">
            أهلاً بك في النسخة الاستعراضية الحية لنظام <strong class="text-white font-bold">DentApex</strong> لإدارة العيادات (تعمل محلياً بالكامل ومزودة بالذكاء الاصطناعي السريري).
          </span>
        </div>

        <!-- Action buttons (CTA + Reset) -->
        <div class="flex items-center gap-2 mr-auto sm:mr-0">
          <!-- Reset Demo Sandbox Button -->
          <button
            type="button"
            @click="handleReset"
            :disabled="resetting"
            class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-white/15 hover:bg-white/25 active:bg-white/30 text-white transition border border-white/20 shadow-xs cursor-pointer disabled:opacity-50"
            title="إعادة شحن البيانات السريرية التجريبية لحالتها الأولى"
          >
            <UIcon
              name="i-heroicons-arrow-path"
              class="w-3.5 h-3.5"
              :class="{ 'animate-spin': resetting }"
            />
            <span>{{ resetting ? 'جاري الضبط...' : 'إعادة ضبط البيانات' }}</span>
          </button>

          <!-- WhatsApp Commercial Purchase CTA Button -->
          <a
            :href="whatsappUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-lg text-xs font-bold bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-white transition shadow-sm hover:shadow-md cursor-pointer border border-emerald-300/30"
          >
            <UIcon name="i-simple-icons-whatsapp" class="w-4 h-4 text-white" />
            <span>طلب النسخة الكاملة للعيادة</span>
          </a>

          <!-- Minimize Toggle -->
          <button
            type="button"
            @click="isMinimized = true"
            class="p-1 rounded-md text-emerald-100 hover:text-white hover:bg-white/10 transition cursor-pointer"
            title="تصغير الشريط"
          >
            <UIcon name="i-heroicons-chevron-up" class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Floating Reopen Pill when Minimized -->
  <div
    v-else-if="isMinimized"
    dir="rtl"
    class="fixed bottom-4 left-4 z-40 flex items-center gap-2"
  >
    <button
      type="button"
      @click="isMinimized = false"
      class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg hover:shadow-xl border border-emerald-400/40 transition hover:scale-105 cursor-pointer"
    >
      <span class="h-2 w-2 rounded-full bg-emerald-300 animate-ping"></span>
      <span>🦷 محاكي DentApex التجريبي</span>
      <UIcon name="i-heroicons-chevron-down" class="w-3.5 h-3.5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDemoStore } from '~/stores/useDemoStore'

const demoStore = useDemoStore()
const toast = useToast()

const isMinimized = ref(false)
const resetting = ref(false)

const isVisible = computed(() => {
  return !isMinimized.value
})

const whatsappPhone = '201000000000'
const whatsappMessage = encodeURIComponent(
  'مرحباً يا هندسة، جربت النسخة الاستعراضية لنظام DentApex وأعجبني جداً. أرغب في الاستفسار عن تفاصيل شراء وترخيص النسخة الكاملة الدائمة لعيادتي.'
)
const whatsappUrl = `https://wa.me/${whatsappPhone}?text=${whatsappMessage}`

async function handleReset() {
  if (resetting.value) return
  resetting.value = true

  try {
    await demoStore.resetDemoData()
    toast.add({
      title: 'تمت إعادة ضبط البيانات التجريبية بنجاح 🔄',
      description: 'تمت استعادة سجلات المرضى الـ 15 ومخطط الأسنان وجدول المواعيد لحالتها الأصلية.',
      color: 'success',
    })
  } catch (err) {
    toast.add({
      title: 'تنبيه',
      description: 'حدث خطأ أثناء إعادة تعيين البيانات.',
      color: 'error',
    })
  } finally {
    resetting.value = false
  }
}
</script>

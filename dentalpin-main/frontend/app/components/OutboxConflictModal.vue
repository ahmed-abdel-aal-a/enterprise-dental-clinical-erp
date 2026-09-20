<template>
  <div
    v-if="activeConflict"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
    dir="rtl"
  >
    <div class="bg-white dark:bg-neutral-900 border border-red-500/30 rounded-xl shadow-2xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in duration-200">
      <div class="flex items-center gap-3 text-red-600 dark:text-red-400">
        <div class="p-2 bg-red-100 dark:bg-red-950/60 rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h3 class="font-bold text-base text-neutral-900 dark:text-white">تعارض في الموعد (الحجز المزدوج)</h3>
          <p class="text-xs text-neutral-500">تم حجز هذا التوقيت مسبقاً على كمبيوتر العيادة</p>
        </div>
      </div>

      <div class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg p-3 text-xs space-y-1.5 text-neutral-800 dark:text-neutral-200">
        <p class="font-medium text-red-800 dark:text-red-300">
          {{ activeConflict.conflict_details?.message || 'هذا الموعد يتعارض مع موعد محجوز مسبقاً.' }}
        </p>
        <div v-if="activeConflict.conflict_details?.conflicting_appointment" class="mt-2 pt-2 border-t border-red-200/60 dark:border-red-900/40 text-neutral-600 dark:text-neutral-400">
          <div>المريض الحاجز: <span class="font-semibold text-neutral-900 dark:text-white">{{ activeConflict.conflict_details.conflicting_appointment.patient_name }}</span></div>
          <div>التوقيت المحجوز: <span class="font-mono text-neutral-900 dark:text-white" dir="ltr">{{ formatTime(activeConflict.conflict_details.conflicting_appointment.start_time) }} - {{ formatTime(activeConflict.conflict_details.conflicting_appointment.end_time) }}</span></div>
        </div>
      </div>

      <div class="space-y-3 pt-2">
        <label class="block text-xs font-medium text-neutral-700 dark:text-neutral-300">
          اختر موعداً جديداً لحل التعارض:
        </label>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <span class="text-[10px] text-neutral-500 block mb-1">وقت البدء</span>
            <input
              type="datetime-local"
              v-model="newStartTime"
              class="w-full text-xs p-2 rounded-md border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white"
            />
          </div>
          <div>
            <span class="text-[10px] text-neutral-500 block mb-1">وقت الانتهاء</span>
            <input
              type="datetime-local"
              v-model="newEndTime"
              class="w-full text-xs p-2 rounded-md border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 pt-3 border-t border-neutral-200 dark:border-neutral-800">
        <button
          type="button"
          @click="handleCancel"
          class="px-3 py-1.5 text-xs text-neutral-600 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-white transition"
        >
          إلغاء الموعد المعلق
        </button>
        <button
          type="button"
          @click="handleResolve"
          class="px-4 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-md shadow-xs transition"
        >
          إعادة الجدولة والمزامنة
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const outbox = useOutbox()
const { activeConflict } = outbox

const newStartTime = ref('')
const newEndTime = ref('')

watch(activeConflict, (item) => {
  if (item && item.payload) {
    if (item.payload.start_time) {
      newStartTime.value = toLocalInputString(item.payload.start_time)
    }
    if (item.payload.end_time) {
      newEndTime.value = toLocalInputString(item.payload.end_time)
    }
  }
})

function toLocalInputString(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    const pad = (n: number) => n.toString().padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return ''
  }
}

function formatTime(isoStr?: string): string {
  if (!isoStr) return ''
  try {
    return new Date(isoStr).toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoStr
  }
}

async function handleResolve() {
  if (!activeConflict.value) return
  const updates: Record<string, any> = {}
  if (newStartTime.value) updates.start_time = new Date(newStartTime.value).toISOString()
  if (newEndTime.value) updates.end_time = new Date(newEndTime.value).toISOString()

  await outbox.resolveConflict(activeConflict.value.id, updates)
}

async function handleCancel() {
  if (!activeConflict.value) return
  await outbox.cancelConflict(activeConflict.value.id)
}
</script>

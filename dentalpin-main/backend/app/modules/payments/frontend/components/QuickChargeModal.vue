<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  open: boolean
  patientId: string
  patientName: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'charged', payload: any): void
}>()

const { createQuickCharge } = usePayments()
const toast = useToast()

const isSubmitting = ref(false)
const description = ref('كشف أولي وفحص وتشخيص')
const amount = ref<number>(200)
const notes = ref('')

const POPULAR_SERVICES = [
  { name: 'كشف أولي وفحص وتشخيص', price: 200, icon: 'i-lucide-stethoscope' },
  { name: 'كشف دوري واستشارة متابعة', price: 100, icon: 'i-lucide-check-check' },
  { name: 'كشف طوارئ وتسكين ألم حاد', price: 250, icon: 'i-lucide-alert-circle' },
  { name: 'أشعة سينية داخل الفم', price: 100, icon: 'i-lucide-scan' },
  { name: 'أشعة بانورامية للفكين', price: 250, icon: 'i-lucide-maximize' },
  { name: 'تنظيف وتلميع وإزالة جير', price: 500, icon: 'i-lucide-sparkles' },
  { name: 'خلع سن بسيط', price: 400, icon: 'i-lucide-scissors' }
]

function selectService(item: { name: string; price: number }) {
  description.value = item.name
  amount.value = item.price
}

async function submitCharge() {
  if (!description.value.trim()) {
    toast.add({ title: 'تنبيه', description: 'يرجى كتابة بيان الخدمة أو الكشف', color: 'amber' })
    return
  }
  if (!amount.value || amount.value <= 0) {
    toast.add({ title: 'تنبيه', description: 'يرجى إدخال مبلغ صحيح', color: 'amber' })
    return
  }

  isSubmitting.value = true
  try {
    const res = await createQuickCharge(props.patientId, {
      description: description.value.trim(),
      amount: amount.value,
      notes: notes.value || undefined
    })

    if (res.success) {
      toast.add({
        title: 'تم تسجيل الخدمة بنجاح',
        description: `تم قيد مبلغ ${amount.value} ج.م على حساب المريض`,
        color: 'green'
      })
      emit('charged', res.data)
      emit('update:open', false)
    } else {
      toast.add({ title: 'خطأ', description: res.error || 'فشل تسجيل الرسوم', color: 'red' })
    }
  } catch (err: any) {
    toast.add({ title: 'خطأ في الاتصال', description: err.message, color: 'red' })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <UModal :open="open" @update:open="$emit('update:open', $event)">
    <template #content>
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100 dark:divide-gray-800' }">
        <template #header>
        <div class="flex items-center justify-between" dir="rtl">
          <div class="flex items-center gap-2">
            <div class="p-2 bg-blue-100 dark:bg-blue-950 text-blue-600 rounded-lg">
              <UIcon name="i-lucide-file-plus-2" class="w-6 h-6" />
            </div>
            <div>
              <h3 class="text-base font-bold text-gray-900 dark:text-white">
                إضافة كشف أو خدمة سريعة
              </h3>
              <p class="text-xs text-gray-500">
                تسجيل رسوم مباشرة على حساب المريض: <span class="font-bold text-gray-700 dark:text-gray-300">{{ patientName }}</span>
              </p>
            </div>
          </div>
          <UButton color="gray" variant="ghost" icon="i-lucide-x" @click="$emit('update:open', false)" />
        </div>
      </template>

      <div class="space-y-4 py-2" dir="rtl">
        <!-- Quick Service Presets -->
        <div>
          <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
            الخدمات والكشوفات السريعة الشائعة
          </label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-48 overflow-y-auto pr-1">
            <button v-for="item in POPULAR_SERVICES" :key="item.name" type="button"
                    @click="selectService(item)"
                    class="flex items-center justify-between p-2 rounded-lg border text-xs transition-all text-right"
                    :class="description === item.name ? 'border-primary-500 bg-primary-50 dark:bg-primary-950 text-primary-900 dark:text-primary-200 ring-1 ring-primary-500' : 'border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'">
              <div class="flex items-center gap-1.5 truncate">
                <UIcon :name="item.icon" class="w-3.5 h-3.5 flex-shrink-0 text-primary-600" />
                <span class="truncate">{{ item.name }}</span>
              </div>
              <span class="font-bold font-mono text-emerald-600 flex-shrink-0 mr-1">{{ item.price }} ج</span>
            </button>
          </div>
        </div>

        <!-- Service Description -->
        <div>
          <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
            اسم أو بيان الخدمة *
          </label>
          <UInput v-model="description" placeholder="مثال: كشف وتشخيص / تنظيف جير / فتح خراج" size="md" />
        </div>

        <!-- Service Amount -->
        <div>
          <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
            قيمة الخدمة المطلوبة (ج.م) *
          </label>
          <UInput v-model.number="amount" type="number" min="0" step="10" size="xl"
                  class="font-mono text-xl font-bold" icon="i-lucide-coins" />
        </div>

        <!-- Notes -->
        <div>
          <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
            ملاحظات الطبيب (اختياري)
          </label>
          <UInput v-model="notes" placeholder="أي تفاصيل أو ملاحظات سريرية تخص هذا الإجراء" size="sm" />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2" dir="rtl">
          <UButton color="gray" variant="soft" @click="$emit('update:open', false)">
            إلغاء
          </UButton>
          <UButton color="primary" icon="i-lucide-check" :loading="isSubmitting"
                   :disabled="!amount || amount <= 0 || !description.trim()" @click="submitCharge">
            إضافة الرسوم ({{ amount || 0 }} ج.م)
          </UButton>
        </div>
      </template>
    </UCard>
  </template>
</UModal>
</template>

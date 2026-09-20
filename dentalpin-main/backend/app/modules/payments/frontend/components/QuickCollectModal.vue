<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { PatientBalance } from '~~/app/types'

const props = defineProps<{
  open: boolean
  patientId: string
  patientName: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'collected', payload: any): void
}>()

const { fetchPatientBalance, recordQuickPayment } = usePayments()
const toast = useToast()

const isLoading = ref(false)
const isSubmitting = ref(false)
const currentBalance = ref<PatientBalance | null>(null)

const amount = ref<number>(0)
const selectedMethod = ref<string>('cash')
const notes = ref<string>('')
const shouldPrintReceipt = ref<boolean>(true)

// Receipt Print State
const showReceiptModal = ref(false)
const lastReceiptData = ref<any>(null)

const PAYMENT_METHODS = [
  { value: 'cash', label: 'نقدي (Cash)', icon: 'i-lucide-banknote', color: 'emerald' },
  { value: 'card', label: 'بطاقة / فيزا (Card)', icon: 'i-lucide-credit-card', color: 'blue' },
  { value: 'instapay', label: 'إنستاباي (InstaPay)', icon: 'i-lucide-smartphone', color: 'purple' },
  { value: 'vodafone_cash', label: 'فودافون كاش (Vodafone)', icon: 'i-lucide-wallet', color: 'rose' },
  { value: 'bank_transfer', label: 'تحويل بنكي', icon: 'i-lucide-building-2', color: 'amber' }
]

// Real-time balance refresh on open to eliminate concurrency race conditions
watch(() => props.open, async (newVal) => {
  if (newVal && props.patientId) {
    isLoading.value = true
    notes.value = ''
    try {
      const bal = await fetchPatientBalance(props.patientId)
      currentBalance.value = bal
      if (bal && bal.has_debt) {
        amount.value = Math.max(0, Number(bal.net_balance))
      } else {
        amount.value = 0
      }
    } catch {
      currentBalance.value = null
    } finally {
      isLoading.value = false
    }
  }
}, { immediate: true })

function setAmount(val: number) {
  amount.value = Math.max(0, Number(val))
}

function addAmount(val: number) {
  amount.value = (Number(amount.value) || 0) + val
}

const remainingDebtAfterPayment = computed(() => {
  if (!currentBalance.value) return 0
  const net = Number(currentBalance.value.net_balance) || 0
  const toPay = Number(amount.value) || 0
  return Math.max(0, net - toPay)
})

async function submitPayment() {
  if (!amount.value || amount.value <= 0) {
    toast.add({ title: 'تنبيه', description: 'يرجى إدخال مبلغ صحيح للتحصيل', color: 'amber' })
    return
  }

  isSubmitting.value = true
  try {
    const res = await recordQuickPayment(
      props.patientId,
      amount.value,
      selectedMethod.value,
      notes.value || 'تحصيل سريع على الحساب'
    )

    if (res.success) {
      toast.add({
        title: 'تم تسجيل التحصيل بنجاح',
        description: `تم استلام ${amount.value} ج.م بنجاح`,
        color: 'green'
      })

      lastReceiptData.value = {
        receiptNumber: `REC-${Date.now().toString().slice(-6)}`,
        patientName: props.patientName,
        amount: amount.value,
        method: selectedMethod.value,
        date: new Date().toLocaleString('ar-EG'),
        notes: notes.value || 'سداد دفعة نقدية',
        remainingBalance: remainingDebtAfterPayment.value
      }

      emit('collected', res.data)
      emit('update:open', false)

      if (shouldPrintReceipt.value) {
        showReceiptModal.value = true
      }
    } else {
      toast.add({ title: 'خطأ', description: res.error || 'فشل تسجيل الدفعة', color: 'red' })
    }
  } catch (err: any) {
    toast.add({ title: 'خطأ في الاتصال', description: err.message, color: 'red' })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div>
    <UModal :open="open" @update:open="$emit('update:open', $event)">
      <template #content>
        <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100 dark:divide-gray-800' }">
          <template #header>
          <div class="flex items-center justify-between" dir="rtl">
            <div class="flex items-center gap-2">
              <div class="p-2 bg-emerald-100 dark:bg-emerald-950 text-emerald-600 rounded-lg">
                <UIcon name="i-lucide-badge-dollar-sign" class="w-6 h-6" />
              </div>
              <div>
                <h3 class="text-base font-bold text-gray-900 dark:text-white">
                  تحصيل نقدية سريع (كاشير العيادة)
                </h3>
                <p class="text-xs text-gray-500">
                  المريض: <span class="font-bold text-gray-700 dark:text-gray-300">{{ patientName }}</span>
                </p>
              </div>
            </div>
            <UButton color="gray" variant="ghost" icon="i-lucide-x" @click="$emit('update:open', false)" />
          </div>
        </template>

        <div v-if="isLoading" class="py-12 text-center text-gray-500" dir="rtl">
          <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin mx-auto mb-2 text-primary-500" />
          <p class="text-sm">جاري جلب الرصيد اللحظي للمريض لمنع أي تعارض...</p>
        </div>

        <div v-else class="space-y-4 py-2" dir="rtl">
          <!-- Real-Time Balance Alert -->
          <div v-if="currentBalance" class="p-3 rounded-lg border flex items-center justify-between"
               :class="currentBalance.has_debt ? 'bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950 dark:border-rose-900 dark:text-rose-200' : 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950 dark:border-emerald-900 dark:text-emerald-200'">
            <div>
              <span class="text-xs font-semibold block">حالة الحساب اللحظية:</span>
              <span class="text-sm font-bold">
                {{ currentBalance.has_debt ? `مستحق على المريض: ${Number(currentBalance.net_balance).toFixed(2)} ج.م` : 'لا توجد مديونية سابقة (الحساب خالص)' }}
              </span>
            </div>
            <UButton v-if="currentBalance.has_debt" size="xs" color="rose" variant="soft"
                     @click="setAmount(Number(currentBalance.net_balance))">
              تصفية الدين بالكامل
            </UButton>
          </div>

          <!-- Amount Input -->
          <div>
            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
              المبلغ المراد تحصيله (ج.م) *
            </label>
            <div class="relative">
              <UInput v-model.number="amount" type="number" min="0" step="10" size="xl"
                      class="font-mono text-xl font-bold" icon="i-lucide-circle-dollar-sign" />
            </div>

            <!-- Quick Presets -->
            <div class="flex flex-wrap gap-1.5 mt-2">
              <UButton size="xs" color="gray" variant="soft" @click="setAmount(100)">100 ج</UButton>
              <UButton size="xs" color="gray" variant="soft" @click="setAmount(200)">200 ج</UButton>
              <UButton size="xs" color="gray" variant="soft" @click="setAmount(500)">500 ج</UButton>
              <UButton size="xs" color="gray" variant="soft" @click="setAmount(1000)">1000 ج</UButton>
              <UButton size="xs" color="gray" variant="ghost" @click="addAmount(50)">+50</UButton>
              <UButton size="xs" color="gray" variant="ghost" @click="addAmount(100)">+100</UButton>
            </div>
          </div>

          <!-- Payment Methods -->
          <div>
            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
              طريقة الدفع *
            </label>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <button v-for="m in PAYMENT_METHODS" :key="m.value" type="button"
                      @click="selectedMethod = m.value"
                      class="flex items-center gap-2 p-2.5 rounded-lg border text-xs font-bold transition-all text-right"
                      :class="selectedMethod === m.value ? 'border-primary-500 bg-primary-50 text-primary-900 dark:bg-primary-950 dark:text-primary-200 ring-2 ring-primary-500/20' : 'border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'">
                <UIcon :name="m.icon" class="w-4 h-4 flex-shrink-0" />
                <span class="truncate">{{ m.label }}</span>
              </button>
            </div>
          </div>

          <!-- Notes -->
          <div>
            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
              ملاحظات أو رقم مرجعي (اختياري)
            </label>
            <UInput v-model="notes" placeholder="مثال: تحويل إنستاباي / دفعة حشو / سداد كشف" size="sm" />
          </div>

          <!-- Print Receipt Toggle -->
          <div class="pt-2 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UCheckbox v-model="shouldPrintReceipt" />
              <span class="text-xs text-gray-700 dark:text-gray-300 font-medium">
                طباعة إيصال استلام نقدية (سند قبض) تلقائياً فور الحفظ
              </span>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2" dir="rtl">
            <UButton color="gray" variant="soft" @click="$emit('update:open', false)">
              إلغاء
            </UButton>
            <UButton color="emerald" icon="i-lucide-check-circle" :loading="isSubmitting"
                     :disabled="isLoading || !amount || amount <= 0" @click="submitPayment">
              تأكيد واستلام {{ amount || 0 }} ج.م
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>

  <!-- Receipt Print Modal -->
  <UModal v-model:open="showReceiptModal">
    <template #content>
      <ReceiptVoucherPrint v-if="lastReceiptData" :receipt-data="lastReceiptData" @close="showReceiptModal = false" />
    </template>
  </UModal>
</div>
</template>

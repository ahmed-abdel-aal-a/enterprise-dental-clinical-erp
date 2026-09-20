<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { PatientLedger, PatientBalance } from '~~/app/types'

const props = defineProps<{
  patientId: string
  patientName: string
}>()

const { fetchPatientLedger, fetchPatientBalance } = usePayments()
const toast = useToast()

const ledger = ref<PatientLedger | null>(null)
const balance = ref<PatientBalance | null>(null)
const isLoading = ref(true)

// Modals
const showCollectModal = ref(false)
const showChargeModal = ref(false)
const showPriceListModal = ref(false)

// Receipt print for specific payment row
const showReceiptModal = ref(false)
const selectedReceiptData = ref<any>(null)

async function loadData() {
  if (!props.patientId) return
  isLoading.value = true
  try {
    const [ledgerData, balData] = await Promise.all([
      fetchPatientLedger(props.patientId),
      fetchPatientBalance(props.patientId)
    ])
    ledger.value = ledgerData
    balance.value = balData
  } catch (err: any) {
    toast.add({ title: 'خطأ', description: 'تعذر تحميل كشف الحساب', color: 'red' })
  } finally {
    isLoading.value = false
  }
}

watch(() => props.patientId, () => {
  loadData()
})

onMounted(() => {
  loadData()
})

function onTransactionRecorded() {
  loadData()
}

function openRowReceipt(entry: any) {
  selectedReceiptData.value = {
    receiptNumber: `REC-${entry.reference_id?.slice(0, 8).toUpperCase() || 'PAY'}`,
    patientName: props.patientName,
    amount: Number(entry.paid_amount || entry.amount || 0),
    method: entry.description || 'نقدي',
    date: new Date(entry.occurred_at).toLocaleString('ar-EG'),
    notes: entry.description,
    remainingBalance: Number(entry.running_balance || 0)
  }
  showReceiptModal.value = true
}

function printLedger() {
  window.print()
}

function formatDate(iso: string) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('ar-EG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="patient-quick-ledger space-y-5" dir="rtl">
    <!-- Header & Action Bar -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-white dark:bg-gray-900 p-4 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
      <div>
        <div class="flex items-center gap-2">
          <div class="p-2 bg-primary-100 dark:bg-primary-950 text-primary-600 rounded-lg">
            <UIcon name="i-lucide-receipt" class="w-5 h-5" />
          </div>
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            كشف الحساب والمدفوعات السريري السريع
          </h2>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          سجل الحسابات المالي الشفاف والرصيد التراكمي المباشر للمريض.
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap gap-2 w-full sm:w-auto print:hidden">
        <UButton color="emerald" icon="i-lucide-hand-coins" size="sm" @click="showCollectModal = true">
          تحصيل نقدية (سداد)
        </UButton>
        <UButton color="blue" variant="soft" icon="i-lucide-plus" size="sm" @click="showChargeModal = true">
          إضافة كشف / خدمة
        </UButton>
        <UButton color="amber" variant="ghost" icon="i-lucide-tags" size="sm" @click="showPriceListModal = true">
          تسعيرة العيادة
        </UButton>
        <UButton color="gray" variant="ghost" icon="i-lucide-printer" size="sm" @click="printLedger">
          طباعة كشف الحساب
        </UButton>
      </div>
    </div>

    <!-- 3 Big KPI Balance Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 1. Total Charged -->
      <div class="bg-white dark:bg-gray-900 p-4 rounded-xl border border-blue-100 dark:border-blue-900/40 shadow-sm relative overflow-hidden">
        <div class="flex justify-between items-start">
          <div>
            <span class="text-xs font-bold text-blue-600 dark:text-blue-400 block mb-1">
              إجمالي الرسوم والكشوفات
            </span>
            <span class="text-2xl font-black text-gray-900 dark:text-white font-mono">
              {{ Number(balance?.total_charged || 0).toFixed(2) }} <span class="text-xs font-normal">ج.م</span>
            </span>
          </div>
          <div class="p-2.5 bg-blue-50 dark:bg-blue-950 text-blue-600 rounded-xl">
            <UIcon name="i-lucide-stethoscope" class="w-6 h-6" />
          </div>
        </div>
        <div class="mt-3 text-[11px] text-gray-500">
          مجموع الخدمات والفحوصات المقدمة للمريض
        </div>
      </div>

      <!-- 2. Total Paid -->
      <div class="bg-white dark:bg-gray-900 p-4 rounded-xl border border-emerald-100 dark:border-emerald-900/40 shadow-sm relative overflow-hidden">
        <div class="flex justify-between items-start">
          <div>
            <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 block mb-1">
              إجمالي المدفوعات المستلمة
            </span>
            <span class="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
              {{ Number(balance?.total_paid || 0).toFixed(2) }} <span class="text-xs font-normal">ج.م</span>
            </span>
          </div>
          <div class="p-2.5 bg-emerald-50 dark:bg-emerald-950 text-emerald-600 rounded-xl">
            <UIcon name="i-lucide-check-check" class="w-6 h-6" />
          </div>
        </div>
        <div class="mt-3 text-[11px] text-gray-500">
          صافي ما تم تحصيله نقدياً وإلكترونياً
        </div>
      </div>

      <!-- 3. Net Balance -->
      <div class="p-4 rounded-xl border shadow-sm relative overflow-hidden transition-all"
           :class="Number(balance?.net_balance || 0) > 0 ? 'bg-rose-50/60 border-rose-200 dark:bg-rose-950/40 dark:border-rose-900' : (Number(balance?.net_balance || 0) < 0 ? 'bg-purple-50/60 border-purple-200 dark:bg-purple-950/40 dark:border-purple-900' : 'bg-emerald-50/60 border-emerald-200 dark:bg-emerald-950/40 dark:border-emerald-900')">
        <div class="flex justify-between items-start">
          <div>
            <span class="text-xs font-bold block mb-1"
                  :class="Number(balance?.net_balance || 0) > 0 ? 'text-rose-700 dark:text-rose-300' : (Number(balance?.net_balance || 0) < 0 ? 'text-purple-700 dark:text-purple-300' : 'text-emerald-700 dark:text-emerald-300')">
              {{ Number(balance?.net_balance || 0) > 0 ? 'الرصيد المتبقي (مديونية)' : (Number(balance?.net_balance || 0) < 0 ? 'رصيد دائن للمريض (مسبق)' : 'حالة الحساب') }}
            </span>
            <span class="text-2xl font-black font-mono tracking-tight"
                  :class="Number(balance?.net_balance || 0) > 0 ? 'text-rose-700 dark:text-rose-300' : (Number(balance?.net_balance || 0) < 0 ? 'text-purple-700 dark:text-purple-300' : 'text-emerald-700 dark:text-emerald-300')">
              {{ Math.abs(Number(balance?.net_balance || 0)).toFixed(2) }} <span class="text-xs font-normal">ج.م</span>
            </span>
          </div>
          <div class="p-2.5 rounded-xl"
               :class="Number(balance?.net_balance || 0) > 0 ? 'bg-rose-100 text-rose-700 dark:bg-rose-900' : (Number(balance?.net_balance || 0) < 0 ? 'bg-purple-100 text-purple-700 dark:bg-purple-900' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900')">
            <UIcon :name="Number(balance?.net_balance || 0) > 0 ? 'i-lucide-alert-triangle' : (Number(balance?.net_balance || 0) < 0 ? 'i-lucide-piggy-bank' : 'i-lucide-shield-check')" class="w-6 h-6" />
          </div>
        </div>
        <div class="mt-3 flex items-center justify-between">
          <span class="text-[11px] font-medium"
                :class="Number(balance?.net_balance || 0) > 0 ? 'text-rose-600 dark:text-rose-400' : (Number(balance?.net_balance || 0) < 0 ? 'text-purple-600 dark:text-purple-400' : 'text-emerald-600 dark:text-emerald-400')">
            {{ Number(balance?.net_balance || 0) > 0 ? 'مستحق السداد فوراً' : (Number(balance?.net_balance || 0) < 0 ? 'مبالغ مدفوعة مقدماً' : 'الحساب خالص بالكامل ✓') }}
          </span>
          <UButton v-if="Number(balance?.net_balance || 0) > 0" size="2xs" color="rose" variant="solid"
                   @click="showCollectModal = true" class="print:hidden">
            تحصيل الآن
          </UButton>
        </div>
      </div>
    </div>

    <!-- Chronological Transactions Table -->
    <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
      <div class="p-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
        <div>
          <h3 class="text-sm font-bold text-gray-900 dark:text-white">
            سجل الحركات المالية المباشر (Running Balance Ledger)
          </h3>
          <p class="text-[11px] text-gray-500">
            تحديث لحظي لكل سداد أو كشف مع الرصيد المتبقي بعد كل حركة مباشرة.
          </p>
        </div>
        <UBadge color="gray" variant="subtle" size="xs">
          {{ ledger?.timeline?.length || 0 }} حركة مسجلة
        </UBadge>
      </div>

      <div v-if="isLoading" class="py-12 text-center text-gray-500">
        <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin mx-auto mb-2 text-primary-500" />
        <p class="text-sm">جاري جلب كشف الحساب...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-xs text-right">
          <thead class="bg-gray-50 dark:bg-gray-800/60 text-gray-600 dark:text-gray-300 font-bold border-b border-gray-200 dark:border-gray-700">
            <tr>
              <th class="py-3 px-3">التاريخ والوقت</th>
              <th class="py-3 px-3">نوع الحركة</th>
              <th class="py-3 px-3">البيان / الخدمة</th>
              <th class="py-3 px-3 text-rose-600 dark:text-rose-400">الرسوم (مدين)</th>
              <th class="py-3 px-3 text-emerald-600 dark:text-emerald-400">المدفوع (دائن)</th>
              <th class="py-3 px-3 bg-gray-100/70 dark:bg-gray-800 font-bold text-gray-900 dark:text-white">الرصيد التراكمي</th>
              <th class="py-3 px-3">المسؤول / الطبيب</th>
              <th class="py-3 px-3 text-center print:hidden">إجراءات</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800 font-sans">
            <tr v-for="entry in ledger?.timeline || []" :key="entry.reference_id"
                class="hover:bg-gray-50/70 dark:hover:bg-gray-800/40 transition-colors">
              <!-- Date -->
              <td class="py-2.5 px-3 text-gray-600 dark:text-gray-400 font-mono text-[11px] whitespace-nowrap">
                {{ formatDate(entry.occurred_at) }}
              </td>

              <!-- Entry Type -->
              <td class="py-2.5 px-3 whitespace-nowrap">
                <UBadge v-if="entry.entry_type === 'payment'" color="emerald" variant="subtle" size="xs">
                  سداد / تحصيل
                </UBadge>
                <UBadge v-else-if="entry.entry_type === 'earned'" color="blue" variant="subtle" size="xs">
                  كشف / خدمة
                </UBadge>
                <UBadge v-else color="amber" variant="subtle" size="xs">
                  مبلغ مسترد
                </UBadge>
              </td>

              <!-- Description -->
              <td class="py-2.5 px-3">
                <span class="font-bold text-gray-800 dark:text-gray-200 block">
                  {{ entry.treatment_name || entry.description || 'معاملة مالية' }}
                </span>
                <span v-if="entry.treatment_status" class="text-[10px] text-gray-400">
                  الحالة: {{ entry.treatment_status }}
                </span>
              </td>

              <!-- Charge (Debit) -->
              <td class="py-2.5 px-3 font-mono font-bold text-rose-600 whitespace-nowrap">
                {{ Number(entry.charge_amount || 0) > 0 ? `${Number(entry.charge_amount).toFixed(2)} ج.م` : '-' }}
              </td>

              <!-- Paid (Credit) -->
              <td class="py-2.5 px-3 font-mono font-bold text-emerald-600 whitespace-nowrap">
                {{ Number(entry.paid_amount || 0) > 0 ? `${Number(entry.paid_amount).toFixed(2)} ج.م` : '-' }}
              </td>

              <!-- Running Balance (From SQL Window Function) -->
              <td class="py-2.5 px-3 font-mono font-extrabold whitespace-nowrap bg-gray-50/50 dark:bg-gray-800/40"
                  :class="Number(entry.running_balance || 0) > 0 ? 'text-rose-600' : (Number(entry.running_balance || 0) < 0 ? 'text-purple-600' : 'text-emerald-600')">
                {{ Number(entry.running_balance || 0) > 0 ? `${Number(entry.running_balance).toFixed(2)} ج.م (عجز)` : (Number(entry.running_balance || 0) < 0 ? `${Math.abs(Number(entry.running_balance)).toFixed(2)} ج.م (زيادة)` : '0.00 ج.م (خالص)') }}
              </td>

              <!-- Professional -->
              <td class="py-2.5 px-3 text-gray-500 whitespace-nowrap">
                {{ entry.professional_name || 'طاقم العيادة' }}
              </td>

              <!-- Row Action -->
              <td class="py-2.5 px-3 text-center print:hidden whitespace-nowrap">
                <UButton v-if="entry.entry_type === 'payment'" size="2xs" color="gray" variant="ghost"
                         icon="i-lucide-printer" title="طباعة سند قبض" @click="openRowReceipt(entry)">
                  إيصال
                </UButton>
              </td>
            </tr>

            <tr v-if="!ledger?.timeline?.length">
              <td colspan="8" class="py-12 text-center text-gray-400">
                <UIcon name="i-lucide-receipt" class="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p class="text-sm font-medium">لا توجد حركات مالية مسجلة لهذا المريض بعد</p>
                <div class="mt-3 flex justify-center gap-2">
                  <UButton size="xs" color="emerald" icon="i-lucide-hand-coins" @click="showCollectModal = true">
                    تسجيل أول دفعة
                  </UButton>
                  <UButton size="xs" color="blue" variant="soft" icon="i-lucide-plus" @click="showChargeModal = true">
                    إضافة كشف أولي
                  </UButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modals -->
    <QuickCollectModal v-model:open="showCollectModal" :patient-id="patientId" :patient-name="patientName"
                       @collected="onTransactionRecorded" />

    <QuickChargeModal v-model:open="showChargeModal" :patient-id="patientId" :patient-name="patientName"
                      @charged="onTransactionRecorded" />

    <QuickPriceListModal v-model:open="showPriceListModal" @updated="loadData" />

    <UModal v-model:open="showReceiptModal">
      <template #content>
        <ReceiptVoucherPrint v-if="selectedReceiptData" :receipt-data="selectedReceiptData" @close="showReceiptModal = false" />
      </template>
    </UModal>
  </div>
</template>

<style scoped>
@media print {
  body * {
    visibility: hidden;
  }
  .patient-quick-ledger,
  .patient-quick-ledger * {
    visibility: visible;
  }
  .patient-quick-ledger {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
  }
}
</style>

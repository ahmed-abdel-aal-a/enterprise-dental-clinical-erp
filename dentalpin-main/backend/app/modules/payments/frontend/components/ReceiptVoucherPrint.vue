<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  receiptData: {
    receiptNumber: string
    patientName: string
    amount: number
    method: string
    date: string
    notes?: string
    remainingBalance?: number
    clinicName?: string
    doctorName?: string
  }
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

function printReceipt() {
  window.print()
}

const methodLabel = computed(() => {
  const map: Record<string, string> = {
    cash: 'نقدي (Cash)',
    card: 'بطاقة / فيزا (Card)',
    instapay: 'إنستاباي (InstaPay)',
    vodafone_cash: 'فودافون كاش (Vodafone Cash)',
    bank_transfer: 'تحويل بنكي',
    other: 'أخرى'
  }
  return map[props.receiptData.method] || props.receiptData.method
})
</script>

<template>
  <div class="receipt-container p-4 bg-white text-gray-900 font-sans" dir="rtl">
    <!-- Header -->
    <div class="text-center pb-3 border-b-2 border-dashed border-gray-300">
      <h2 class="text-xl font-bold tracking-tight text-primary-700">
        {{ receiptData.clinicName || 'عيادة DentApex لطب وجراحة الفم والأسنان' }}
      </h2>
      <p v-if="receiptData.doctorName" class="text-xs text-gray-600 mt-1 font-medium">
        {{ receiptData.doctorName }}
      </p>
      <div class="inline-block mt-2 px-3 py-1 bg-gray-100 rounded-full text-xs font-bold text-gray-700">
        إيصال استلام نقدية / سند قبض
      </div>
    </div>

    <!-- Meta Info -->
    <div class="py-3 text-xs border-b border-dashed border-gray-200 space-y-1.5">
      <div class="flex justify-between">
        <span class="text-gray-500">رقم الإيصال:</span>
        <span class="font-mono font-bold">{{ receiptData.receiptNumber }}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-500">التاريخ والوقت:</span>
        <span>{{ receiptData.date }}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-500">اسم المريض:</span>
        <span class="font-bold text-gray-800">{{ receiptData.patientName }}</span>
      </div>
    </div>

    <!-- Amount Received Box -->
    <div class="my-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-center">
      <span class="text-xs text-emerald-700 block font-medium">المبلغ المستلم</span>
      <span class="text-2xl font-black text-emerald-800 tracking-tight">
        {{ Number(receiptData.amount).toFixed(2) }} <span class="text-sm font-normal">ج.م</span>
      </span>
      <span class="text-[11px] text-emerald-600 block mt-0.5">
        طريقة السداد: {{ methodLabel }}
      </span>
    </div>

    <!-- Financial Details -->
    <div class="text-xs space-y-1.5 py-2 border-b border-dashed border-gray-200">
      <div v-if="receiptData.notes" class="flex justify-between">
        <span class="text-gray-500">البيان / ملاحظات:</span>
        <span class="text-gray-700">{{ receiptData.notes }}</span>
      </div>
      <div v-if="receiptData.remainingBalance !== undefined" class="flex justify-between font-medium">
        <span class="text-gray-600">الرصيد المتبقي على الحساب:</span>
        <span :class="Number(receiptData.remainingBalance) > 0 ? 'text-rose-600 font-bold' : 'text-emerald-600 font-bold'">
          {{ Number(receiptData.remainingBalance) > 0 ? `${Number(receiptData.remainingBalance).toFixed(2)} ج.م (متبقي)` : '0.00 ج.م (خالص الحساب)' }}
        </span>
      </div>
    </div>

    <!-- Footer Signatures -->
    <div class="mt-6 pt-2 flex justify-between items-end text-xs text-gray-500">
      <div class="text-center">
        <p class="mb-6">توقيع المستلم / الكاشير</p>
        <div class="w-24 border-b border-gray-400"></div>
      </div>
      <div class="text-center">
        <p class="mb-6">ختم العيادة</p>
        <div class="w-20 border-b border-gray-400"></div>
      </div>
    </div>

    <!-- Bottom Thank You -->
    <div class="text-center text-[10px] text-gray-400 mt-6 print:mt-4">
      نتمنى لكم دوام الصحة والعافية · DentApex Clinic System
    </div>

    <!-- Screen-only Action Buttons -->
    <div class="mt-6 flex gap-2 justify-end print:hidden">
      <UButton color="gray" variant="soft" icon="i-lucide-x" @click="$emit('close')">
        إغلاق
      </UButton>
      <UButton color="primary" icon="i-lucide-printer" @click="printReceipt">
        طباعة الإيصال (Print)
      </UButton>
    </div>
  </div>
</template>

<style scoped>
@media print {
  body * {
    visibility: hidden;
  }
  .receipt-container,
  .receipt-container * {
    visibility: visible;
  }
  .receipt-container {
    position: fixed;
    left: 0;
    top: 0;
    width: 80mm !important;
    max-width: 80mm !important;
    margin: 0;
    padding: 8px !important;
    box-shadow: none !important;
    font-size: 11px !important;
  }
}
</style>

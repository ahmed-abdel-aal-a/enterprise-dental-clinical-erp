<script setup lang="ts">
/**
 * "Asignar a presupuesto" — reallocate a whole payment (typically an
 * anticipo left on account) to one of the patient's budgets via
 * `POST /payments/{id}/reallocate`. Billing mirrors the allocation onto
 * the budget's invoices transactionally (issue #178), so this is also
 * the "apply to invoice" action reception was missing.
 */
import type { PaymentRecord } from '~~/app/types'

const props = defineProps<{
  open: boolean
  paymentId: string
  patientId: string
  amount: number
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'reallocated', payment: PaymentRecord): void
}>()

const { t } = useI18n()
const { reallocate } = usePayments()
const { format: formatCurrency } = useCurrency()
const toast = useToast()

const target = ref('')
const isSubmitting = ref(false)
const errorMsg = ref<string | null>(null)

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    target.value = ''
    errorMsg.value = null
  }
})

async function submit() {
  if (!target.value) return
  isSubmitting.value = true
  errorMsg.value = null
  try {
    const updated = await reallocate(props.paymentId, {
      allocations: [{ target_type: 'budget', target_id: target.value, amount: props.amount }]
    })
    if (updated) {
      toast.add({ title: t('payments.reallocate.success'), color: 'success' })
      emit('reallocated', updated)
      emit('update:open', false)
    } else {
      errorMsg.value = t('payments.reallocate.error')
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <UModal
    :open="open"
    :title="t('payments.reallocate.title')"
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <div class="space-y-4">
        <p class="text-sm text-muted">
          {{ t('payments.reallocate.hint', { amount: formatCurrency(amount) }) }}
        </p>
        <UFormField :label="t('payments.target.label')">
          <AllocationTargetSelect
            v-model="target"
            :patient-id="patientId"
            budgets-only
          />
        </UFormField>
        <p
          v-if="errorMsg"
          class="text-sm text-danger-accent"
        >
          {{ errorMsg }}
        </p>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <UButton
          variant="ghost"
          @click="emit('update:open', false)"
        >
          {{ t('payments.new.cancel') }}
        </UButton>
        <UButton
          :disabled="!target || isSubmitting"
          :loading="isSubmitting"
          @click="submit"
        >
          {{ t('payments.reallocate.submit') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>

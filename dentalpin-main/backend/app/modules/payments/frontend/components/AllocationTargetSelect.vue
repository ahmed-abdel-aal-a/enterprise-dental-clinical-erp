<script setup lang="ts">
/**
 * "Where does this money go?" — a single select over the patient's
 * open budgets plus "A cuenta". Value is ``'on_account'`` or a budget
 * id. Used by PaymentCreateModal (main destination + advanced split
 * rows) and by PaymentReallocateModal (issue #178: no more raw UUIDs).
 */
import type { BudgetListItem, PaginatedResponse } from '~~/app/types'

const props = defineProps<{
  patientId: string
  modelValue: string
  disabled?: boolean
  /** Hide the on-account option (reallocate flow: only budgets make sense). */
  budgetsOnly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'loaded', budgets: BudgetListItem[]): void
}>()

const { t } = useI18n()
const api = useApi()
const { format: formatCurrency } = useCurrency()

const budgets = ref<BudgetListItem[]>([])

async function load() {
  if (!props.patientId) {
    budgets.value = []
    return
  }
  try {
    const params = new URLSearchParams({ patient_id: props.patientId, page_size: '100' })
    params.append('status', 'accepted')
    params.append('status', 'completed')
    const res = await api.get<PaginatedResponse<BudgetListItem>>(`/api/v1/budget/budgets?${params}`)
    budgets.value = res.data
  } catch {
    budgets.value = []
  }
  emit('loaded', budgets.value)
}

watch(() => props.patientId, load, { immediate: true })

const items = computed(() => {
  const list = budgets.value.map(b => ({
    label: `${b.budget_number} · ${formatCurrency(Number(b.total))}`,
    value: b.id
  }))
  return props.budgetsOnly
    ? list
    : [{ label: t('payments.target.onAccount'), value: 'on_account' }, ...list]
})

defineExpose({ budgets })
</script>

<template>
  <USelect
    :model-value="modelValue"
    :items="items"
    :disabled="disabled || items.length === 0"
    :placeholder="t('payments.target.placeholder')"
    class="w-full"
    @update:model-value="emit('update:modelValue', $event as string)"
  />
</template>

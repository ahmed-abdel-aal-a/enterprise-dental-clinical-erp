<script setup lang="ts">
/**
 * AdministrationModeToggle — full-width pill-bar over administration
 * tab modes with contextual badges (budgets count, debt amount).
 *
 * The `payments` mode is contributed by the `payments` module via the
 * `patient.detail.administracion.payments` slot. The pill only appears
 * when the slot has at least one provider that the current user can see
 * — i.e. the module is installed AND the user has `payments.record.read`.
 * No direct dependency from `patients` to `payments`: we only probe the
 * slot registry.
 */
import { useModuleSlots } from '~~/app/composables/useModuleSlots'

export type AdministrationMode = 'budgets' | 'billing' | 'payments' | 'documents'

interface ModeBadges {
  budgets?: string | number
  billing?: string | number
  payments?: string | number
  documents?: string | number
}

interface ModeBadgeColors {
  budgets?: 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info'
  billing?: 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info'
  payments?: 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info'
  documents?: 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info'
}

const props = defineProps<{
  modelValue: AdministrationMode
  badges?: ModeBadges
  badgeColors?: ModeBadgeColors
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: AdministrationMode]
}>()

const { t } = useI18n()
const { resolve } = useModuleSlots()

const paymentsAvailable = computed(() =>
  resolve('patient.detail.administracion.payments', {}).length > 0
)

const options = computed(() => {
  const base = [
    {
      value: 'budgets',
      label: t('patientDetail.tabs.budgets'),
      icon: 'i-lucide-file-text',
      badge: props.badges?.budgets,
      badgeColor: props.badgeColors?.budgets ?? 'neutral'
    },
    {
      value: 'billing',
      label: t('patientDetail.tabs.billing'),
      icon: 'i-lucide-receipt',
      badge: props.badges?.billing,
      badgeColor: props.badgeColors?.billing ?? 'neutral'
    }
  ]
  if (paymentsAvailable.value) {
    base.push({
      value: 'payments',
      label: t('patientDetail.tabs.payments'),
      icon: 'i-lucide-wallet',
      badge: props.badges?.payments,
      badgeColor: props.badgeColors?.payments ?? 'neutral'
    })
  }
  base.push({
    value: 'documents',
    label: t('patientDetail.tabs.documents'),
    icon: 'i-lucide-files',
    badge: props.badges?.documents,
    badgeColor: props.badgeColors?.documents ?? 'neutral'
  })
  return base
})
</script>

<template>
  <SegmentedControl
    :model-value="modelValue"
    :options="options"
    full-width
    @update:model-value="(v) => emit('update:modelValue', v as AdministrationMode)"
  />
</template>

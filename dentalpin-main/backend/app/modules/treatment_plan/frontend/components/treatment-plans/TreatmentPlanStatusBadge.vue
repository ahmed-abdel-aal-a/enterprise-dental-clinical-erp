<script setup lang="ts">
import type { TreatmentPlanStatus } from '~~/app/types'
import type { UiColor } from '~~/app/config/severity'

const props = defineProps<{
  status: TreatmentPlanStatus
  size?: 'xs' | 'sm' | 'md'
}>()

const { t } = useI18n()

const colorMap: Record<TreatmentPlanStatus, UiColor> = {
  draft: 'neutral',
  pending: 'warning',
  active: 'info',
  completed: 'success',
  closed: 'error',
  archived: 'neutral'
}

const color = computed(() => colorMap[props.status])
const label = computed(() => t(`treatmentPlans.status.${props.status}`))
</script>

<template>
  <UBadge
    :color="color"
    :size="size || 'sm'"
    variant="subtle"
  >
    {{ label }}
  </UBadge>
</template>

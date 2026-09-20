<script setup lang="ts">
export interface AppointmentResult {
  id: string
  patient_name?: string | null
  start_time: string
  end_time?: string | null
  status?: string
  cabinet?: string | null
}

const props = defineProps<{ appointment: AppointmentResult }>()
const { t } = useI18n()
const { timeRange } = useCopilotFormat()

type BadgeColor = 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'

const STATUS_COLOR: Record<string, BadgeColor> = {
  scheduled: 'neutral',
  confirmed: 'info',
  checked_in: 'info',
  in_treatment: 'warning',
  completed: 'success',
  cancelled: 'error',
  no_show: 'warning'
}

const statusColor = computed<BadgeColor>(() => STATUS_COLOR[props.appointment.status ?? ''] ?? 'neutral')
const statusLabel = computed(() =>
  props.appointment.status ? t(`copilot.apptStatus.${props.appointment.status}`) : ''
)
</script>

<template>
  <div class="rounded-lg border border-default bg-elevated p-3">
    <div class="flex items-center justify-between gap-2">
      <span class="flex items-center gap-1.5 text-sm font-medium">
        <UIcon
          name="i-lucide-calendar"
          class="text-muted"
        />
        {{ timeRange(appointment.start_time, appointment.end_time ?? undefined) }}
      </span>
      <UBadge
        v-if="statusLabel"
        :color="statusColor"
        variant="subtle"
        size="sm"
      >
        {{ statusLabel }}
      </UBadge>
    </div>
    <div class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
      <span
        v-if="appointment.patient_name"
        class="flex items-center gap-1"
      >
        <UIcon name="i-lucide-user" />
        {{ appointment.patient_name }}
      </span>
      <span
        v-if="appointment.cabinet"
        class="flex items-center gap-1"
      >
        <UIcon name="i-lucide-armchair" />
        {{ appointment.cabinet }}
      </span>
    </div>
  </div>
</template>

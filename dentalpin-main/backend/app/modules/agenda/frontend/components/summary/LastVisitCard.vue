<script setup lang="ts">
/**
 * LastVisitCard — smart-card for the patient Resumen grid (issue #182).
 *
 * Registered in ``patient.summary.cards`` by the agenda module, right
 * next to ``NextAppointmentCard``. Shows the patient's most recent
 * completed appointment so reception can tell a first-timer from a
 * regular without leaving the Summary tab. A patient with no completed
 * appointments gets an explicit "never visited" empty state.
 */
import type { Appointment, PaginatedResponse, PatientExtended } from '~~/app/types'
import { parseWallClock } from '~~/app/utils/wallClock'

interface Ctx {
  patient: PatientExtended
}

const props = defineProps<{ ctx: Ctx }>()

const { t, locale } = useI18n()
const api = useApi()

const patientId = computed(() => props.ctx.patient.id)

const { data, status } = await useAsyncData(
  () => `agenda:summary-card:last-visit:${patientId.value}`,
  async () => {
    try {
      return await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?patient_id=${patientId.value}&status=completed&order=desc&page_size=1`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 1 }
    }
  },
  { watch: [patientId], server: false }
)

const lastVisit = computed<Appointment | null>(() => data.value?.data[0] ?? null)

const dayLabel = computed(() => {
  if (!lastVisit.value) return ''
  const visit = new Date(lastVisit.value.start_time)
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const days = Math.round((startOfDay(new Date()) - startOfDay(visit)) / (1000 * 60 * 60 * 24))
  if (days === 0) return t('appointments.today', 'Hoy')
  if (days === 1) return t('appointments.yesterday', 'Ayer')
  return visit.toLocaleDateString(locale.value, { day: 'numeric', month: 'short', year: 'numeric' })
})

const timeLabel = computed(() => {
  if (!lastVisit.value) return ''
  return parseWallClock(lastVisit.value.start_time).toLocaleTimeString(locale.value, {
    hour: '2-digit',
    minute: '2-digit'
  })
})

const href = computed(() => {
  if (!lastVisit.value) {
    // Never visited — same target as the next-appointment empty state:
    // the agenda with the patient pre-selected for booking.
    return `/appointments?patient_id=${patientId.value}`
  }
  const date = lastVisit.value.start_time.split('T')[0]
  return `/appointments?highlight=${lastVisit.value.id}&date=${date}`
})

const professionalName = computed(() => {
  const p = lastVisit.value?.professional
  if (!p) return ''
  return [p.first_name, p.last_name].filter(Boolean).join(' ')
})
</script>

<template>
  <SummaryCard
    :title="t('patientDetail.lastVisit', 'Última visita')"
    icon="i-lucide-calendar-check"
    severity="neutral"
    :loading="status === 'pending'"
    :empty="!lastVisit"
    :to="href"
  >
    <template #empty>
      {{ t('patientDetail.neverVisited', 'Sin visitas previas') }}
    </template>

    <div class="space-y-1">
      <div class="flex items-baseline gap-2 flex-wrap">
        <span class="text-h2 text-default">{{ dayLabel }}</span>
        <span class="text-ui text-muted tnum">{{ timeLabel }}</span>
      </div>
      <p
        v-if="professionalName"
        class="text-caption text-muted truncate"
      >
        {{ professionalName }}
      </p>
      <p
        v-if="lastVisit?.treatment_type"
        class="text-caption text-subtle truncate"
      >
        {{ lastVisit.treatment_type }}
      </p>
    </div>

    <template #footer>
      <span>{{ lastVisit ? t('patientDetail.openAppointment', 'Abrir cita') : t('patientDetail.scheduleAppointment', 'Agendar') }}</span>
    </template>
  </SummaryCard>
</template>

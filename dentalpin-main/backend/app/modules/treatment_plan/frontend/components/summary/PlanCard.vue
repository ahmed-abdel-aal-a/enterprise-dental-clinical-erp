<script setup lang="ts">
/**
 * PlanCard — smart-card for the patient Resumen grid.
 *
 * Registered into ``patient.summary.cards`` by the treatment_plan
 * module's slot plugin. Receives ``ctx = { patient }`` from the host
 * (``patients``) which never imports this file.
 *
 * Snapshot: active plan name, progress bar, n/m completion. Deep link
 * goes straight into the plan detail (not the plans list), saving one
 * click vs. the old IA.
 */
import type { PatientExtended, TreatmentPlan, PaginatedResponse } from '~~/app/types'

interface Ctx {
  patient: PatientExtended
}

const props = defineProps<{ ctx: Ctx }>()

const { t } = useI18n()
const api = useApi()

const patientId = computed(() => props.ctx.patient.id)

const { data, status } = await useAsyncData(
  () => `treatment_plan:summary-card:${patientId.value}`,
  async () => {
    try {
      return await api.get<PaginatedResponse<TreatmentPlan>>(
        `/api/v1/treatment_plan/treatment-plans?patient_id=${patientId.value}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  },
  { watch: [patientId], server: false }
)

const activePlan = computed<TreatmentPlan | null>(() => {
  const plans = data.value?.data ?? []
  return plans.find(p => p.status === 'active')
    ?? plans.find(p => p.status === 'pending')
    ?? plans.find(p => p.status === 'draft')
    ?? null
})

const totalCount = computed(() => activePlan.value?.item_count ?? 0)
const completedCount = computed(() => activePlan.value?.completed_count ?? 0)
const progress = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((completedCount.value / totalCount.value) * 100)
})

const planHref = computed(() =>
  activePlan.value
    ? `/treatment-plans/${activePlan.value.id}?from=patient&patientId=${patientId.value}`
    : `/patients/${patientId.value}?tab=clinical&action=createPlan`
)

const severity = computed<'neutral' | 'info' | 'success'>(() => {
  if (!activePlan.value) return 'neutral'
  if (progress.value >= 80) return 'success'
  return 'info'
})

const planTitle = computed(() => activePlan.value?.title || activePlan.value?.plan_number || '')
</script>

<template>
  <SummaryCard
    :title="t('patientDetail.activePlan', 'Plan activo')"
    icon="i-lucide-target"
    :severity="severity"
    :loading="status === 'pending'"
    :empty="!activePlan"
    :to="planHref"
  >
    <template #empty>
      {{ t('patientDetail.noActivePlan', 'Sin planes activos') }}
    </template>

    <div class="space-y-2">
      <p class="text-ui text-default line-clamp-2">
        {{ planTitle }}
      </p>
      <div>
        <div class="flex justify-between items-center mb-1 text-caption">
          <span class="text-subtle tnum">
            {{ completedCount }}/{{ totalCount }} {{ t('treatmentPlans.treatments', 'tratamientos') }}
          </span>
          <span class="text-primary-accent tnum">{{ progress }}%</span>
        </div>
        <div class="w-full bg-surface-sunken rounded-full h-1.5 overflow-hidden">
          <div
            class="h-full rounded-full transition-[width] duration-300"
            :style="{ width: `${progress}%`, backgroundColor: 'var(--color-primary)' }"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <span>{{ activePlan ? t('patientDetail.viewPlan', 'Abrir plan') : t('patientDetail.createPlan', 'Crear plan') }}</span>
    </template>
  </SummaryCard>
</template>

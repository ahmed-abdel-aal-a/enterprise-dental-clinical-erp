<script setup lang="ts">
/**
 * NewBudgetPlanHint — nudge on the "New quote" form (issue #177).
 *
 * Registered into ``budget.new.form`` by the treatment_plan slot plugin;
 * receives ``ctx = { patient }`` from the host (``budget``), which never
 * imports this file. A quote typed here by hand would never be linked to
 * the patient's plan (the link is written only when a plan is confirmed),
 * so when the patient has a draft/pending plan without a quote we say so
 * and send the user to the plan instead.
 */
import type { Patient, PaginatedResponse, TreatmentPlan } from '~~/app/types'

interface Ctx {
  patient: Patient | null
}

const props = defineProps<{ ctx: Ctx }>()

const { t } = useI18n()
const api = useApi()

const patientId = computed(() => props.ctx.patient?.id ?? null)

const { data } = await useAsyncData(
  () => `treatment_plan:new-budget-hint:${patientId.value ?? 'none'}`,
  async () => {
    if (!patientId.value) return []
    try {
      const res = await api.get<PaginatedResponse<TreatmentPlan>>(
        `/api/v1/treatment_plan/treatment-plans?patient_id=${patientId.value}`
      )
      return res.data
    } catch {
      return []
    }
  },
  { watch: [patientId], server: false, default: () => [] }
)

const plansWithoutQuote = computed(() =>
  (data.value ?? []).filter(
    p => (p.status === 'draft' || p.status === 'pending') && !p.budget_id
  )
)
</script>

<template>
  <UAlert
    v-for="plan in plansWithoutQuote"
    :key="plan.id"
    color="warning"
    variant="subtle"
    icon="i-lucide-clipboard-list"
    :description="t('treatmentPlans.newBudgetHint.text', { plan: plan.title ? `${plan.plan_number} — ${plan.title}` : plan.plan_number })"
    :actions="[{ label: t('treatmentPlans.newBudgetHint.cta'), to: `/treatment-plans/${plan.id}`, color: 'warning', variant: 'solid' }]"
  />
</template>

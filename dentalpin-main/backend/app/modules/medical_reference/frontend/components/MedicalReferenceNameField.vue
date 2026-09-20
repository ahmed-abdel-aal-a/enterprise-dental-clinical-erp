<script setup lang="ts">
/**
 * MedicalReferenceNameField — adapter between patients_clinical's
 * ``patients_clinical.medical_history.<entity>_name`` slot contract and
 * ReferenceSearchInput.
 *
 * Registered into those slots by this module's own plugin
 * (../plugins/slots.client.ts). The host form never imports this file —
 * the slot names are the only contract, so nothing breaks when
 * medical_reference isn't installed (the form falls back to its plain
 * input and entries simply carry no reference_id).
 */
import type { ReferenceKind } from '../composables/useMedicalReference'

/** Mirrors the ctx contract documented in patients_clinical's
 * MedicalHistoryForm.vue — duplicated deliberately, importing it would
 * re-create the cross-module dependency the slots exist to avoid. */
interface MedicalHistoryNameFieldCtx {
  kind: 'allergy' | 'medication' | 'disease' | 'surgery'
  value: string
  placeholder?: string
  disabled?: boolean
  select: (name: string, referenceId: string | null) => void
}

const props = defineProps<{ ctx: MedicalHistoryNameFieldCtx }>()

const KIND_BY_ENTITY: Record<MedicalHistoryNameFieldCtx['kind'], ReferenceKind> = {
  allergy: 'allergies',
  medication: 'medications',
  disease: 'diseases',
  surgery: 'surgeries'
}

const kind = computed(() => KIND_BY_ENTITY[props.ctx.kind])

// Local mirror of the picked/created item. The host owns the persisted
// entry; we only report commits back through ctx.select().
const name = ref(props.ctx.value)
const referenceId = ref<string | null>(null)

// The host resets its entry after adding it to the list (ctx.value goes
// back to ''); follow along or the combobox keeps showing the previous
// selection. An externally-set value has no known reference row, so the
// mirror id is dropped rather than guessed.
watch(
  () => props.ctx.value,
  (value) => {
    if (value === name.value) return
    name.value = value
    referenceId.value = null
  }
)

function commit(nextName: string, nextReferenceId: string | null) {
  name.value = nextName
  referenceId.value = nextReferenceId
  props.ctx.select(nextName, nextReferenceId)
}
</script>

<template>
  <ReferenceSearchInput
    :kind="kind"
    :model-value="name"
    :reference-id="referenceId"
    :placeholder="ctx.placeholder"
    :disabled="ctx.disabled"
    @update:model-value="(v: string) => commit(v, referenceId)"
    @update:reference-id="(v: string | null) => commit(name, v)"
  />
</template>

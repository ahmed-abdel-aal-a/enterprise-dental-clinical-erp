<script setup lang="ts">
import { PERMISSIONS } from '~~/app/config/permissions'
import type { Patient } from '~/types'
import { useLabOrders, type WorkType, type ImpressionType, type Shade, VITA_CLASSICAL_SHADES } from '../../composables/useLabOrders'

definePageMeta({ middleware: ['auth'] })

const { t } = useI18n()
const { can } = usePermissions()
const labOrdersApi = useLabOrders()
const contactsApi = useContacts()

if (!can(PERMISSIONS.labOrders.write)) await navigateTo('/lab-orders')

const workTypes: WorkType[] = ['crown', 'bridge', 'denture', 'implant', 'veneer', 'orthodontic', 'repair', 'other']
const impressionTypes: ImpressionType[] = ['alginate', 'pvs_silicone', 'digital_scan', 'other']
const selectedPatient = ref<Patient | null>(null)
const labs = ref<{ id: string, name: string }[]>([])
const saving = ref(false)
const form = ref({
  lab_contact_id: '',
  work_type: 'crown' as WorkType,
  tooth_reference: '',
  impression_type: undefined as ImpressionType | undefined,
  antagonist_info: '',
  shade: undefined as Shade | undefined,
  sent_date: new Date().toISOString().slice(0, 10),
  expected_date: '',
  notes: ''
})

onMounted(async () => {
  const response = await contactsApi.list({ contact_type: 'lab', page: 1, page_size: 100 })
  labs.value = response.data.map(contact => ({ id: contact.id, name: contact.name }))
  form.value.lab_contact_id = labs.value[0]?.id ?? ''
})

async function submit() {
  if (!selectedPatient.value || !form.value.lab_contact_id) return
  saving.value = true
  try {
    await labOrdersApi.create({
      patient_id: selectedPatient.value.id,
      lab_contact_id: form.value.lab_contact_id,
      work_type: form.value.work_type,
      tooth_reference: form.value.tooth_reference || null,
      impression_type: form.value.impression_type ?? null,
      antagonist_info: form.value.antagonist_info || null,
      shade: form.value.shade ?? null,
      sent_date: form.value.sent_date,
      expected_date: form.value.expected_date || null,
      notes: form.value.notes || null
    })
    await navigateTo('/lab-orders')
  } finally { saving.value = false }
}
</script>

<template>
  <div class="p-4 space-y-4 max-w-xl">
    <h1 class="text-h2 text-default">
      {{ t('labOrders.add') }}
    </h1>
    <p
      v-if="labs.length === 0"
      class="text-caption text-subtle"
    >
      {{ t('labOrders.noLabsHint') }}
    </p>
    <PatientSearch
      v-model="selectedPatient"
      :placeholder="t('labOrders.selectPatient')"
    />
    <USelect
      v-model="form.lab_contact_id"
      :items="labs.map(lab => ({ value: lab.id, label: lab.name }))"
      :placeholder="t('labOrders.selectLab')"
    />
    <USelect
      v-model="form.work_type"
      :items="workTypes.map(value => ({ value, label: t(`labOrders.workTypes.${value}`) }))"
    />
    <UInput
      v-model="form.tooth_reference"
      :placeholder="t('labOrders.tooth')"
    />
    <USelect
      v-model="form.impression_type"
      :items="impressionTypes.map(value => ({ value, label: t(`labOrders.impressionTypes.${value}`) }))"
      :placeholder="t('labOrders.impressionType')"
    />
    <UInput
      v-model="form.antagonist_info"
      :placeholder="t('labOrders.antagonistInfo')"
    />
    <USelect
      v-model="form.shade"
      :items="VITA_CLASSICAL_SHADES.map(value => ({ value, label: value }))"
      :placeholder="t('labOrders.shade')"
    />
    <UInput
      v-model="form.sent_date"
      type="date"
    />
    <UInput
      v-model="form.expected_date"
      type="date"
      :placeholder="t('labOrders.expectedDate')"
    />
    <UTextarea
      v-model="form.notes"
      :placeholder="t('labOrders.notes')"
    />
    <div class="flex justify-end gap-2">
      <UButton
        variant="ghost"
        to="/lab-orders"
      >
        {{ t('labOrders.cancel') }}
      </UButton>
      <UButton
        :loading="saving"
        :disabled="!selectedPatient || !form.lab_contact_id"
        @click="submit"
      >
        {{ t('labOrders.save') }}
      </UButton>
    </div>
  </div>
</template>

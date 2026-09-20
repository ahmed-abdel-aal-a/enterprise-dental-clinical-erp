import type { ApiResponse } from '~~/app/types'

export interface PatientRelationship {
  id: string
  patient_id: string
  related_patient_id: string
  related_patient_name: string
  relationship_type: 'parent' | 'child' | 'spouse' | 'sibling' | 'guardian' | 'ward' | 'other'
  notes?: string
  created_at: string
}

export function usePatientRelationships(patientId: Ref<string | undefined>) {
  const api = useApi()
  const { t } = useI18n()
  const toast = useToast()

  const relationships = ref<PatientRelationship[]>([])
  const isLoading = ref(false)
  const isSaving = ref(false)

  async function fetchAll() {
    if (!patientId.value) return
    isLoading.value = true
    try {
      const res = await api.get<ApiResponse<PatientRelationship[]>>(
        `/api/v1/patient_relationships/patients/${patientId.value}/relationships`
      )
      relationships.value = res.data || []
    } catch (e) {
      console.error('Failed to fetch patient relationships:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function addRelationship(data: {
    related_patient_id: string
    relationship_type: string
    notes?: string
  }): Promise<boolean> {
    if (!patientId.value) return false
    isSaving.value = true
    try {
      const res = await api.post<ApiResponse<PatientRelationship>>(
        `/api/v1/patient_relationships/patients/${patientId.value}/relationships`,
        data
      )
      relationships.value.push(res.data)
      toast.add({
        title: t('common.success'),
        description: t('patientRelationships.relationships.addSuccess'),
        color: 'success'
      })
      return true
    } catch (e: unknown) {
      const err = e as { data?: { detail?: string } }
      toast.add({
        title: t('common.error'),
        description: err?.data?.detail || t('patientRelationships.relationships.addError'),
        color: 'error'
      })
      console.error('Failed to add relationship:', e)
      return false
    } finally {
      isSaving.value = false
    }
  }

  async function removeRelationship(relationshipId: string): Promise<boolean> {
    if (!patientId.value) return false
    try {
      await api.del(
        `/api/v1/patient_relationships/patients/${patientId.value}/relationships/${relationshipId}`
      )
      relationships.value = relationships.value.filter(r => r.id !== relationshipId)
      return true
    } catch (e) {
      toast.add({
        title: t('common.error'),
        description: t('patientRelationships.relationships.removeError'),
        color: 'error'
      })
      console.error('Failed to remove relationship:', e)
      return false
    }
  }

  return {
    relationships,
    isLoading,
    isSaving,
    fetchAll,
    addRelationship,
    removeRelationship
  }
}

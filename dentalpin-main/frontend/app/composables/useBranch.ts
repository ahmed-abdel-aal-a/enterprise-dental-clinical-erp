import type { Branch, BranchCreate, BranchUpdate, ApiResponse } from '~/types'

const DEFAULT_DEMO_BRANCH: Branch = {
  id: 'br-main',
  clinic_id: 'demo-clinic-00000000-0000-0000-0000-000000000001',
  name: 'الفرع الرئيسي (وسط البلد)',
  code: 'MAIN',
  address: 'شارع التحرير، وسط البلد، القاهرة',
  phone: '+201000000000',
  is_main: true,
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z'
}

export function useBranchState() {
  return {
    branches: useState<Branch[]>('clinic:branches', () => [DEFAULT_DEMO_BRANCH]),
    currentBranch: useState<Branch | null>('clinic:current_branch', () => DEFAULT_DEMO_BRANCH),
    isLoading: useState<boolean>('clinic:branches_loading', () => false)
  }
}

export function useBranch() {
  const api = useApi()
  const auth = useAuth()
  const toast = useToast()
  const { t } = useI18n()

  const { branches, currentBranch, isLoading } = useBranchState()

  const activeBranches = computed(() => branches.value.filter(b => b.is_active))
  const mainBranch = computed(() => branches.value.find(b => b.is_main) || branches.value[0] || null)

  const BRANCH_STORAGE_KEY = 'dentapex_active_branch_id'

  async function fetchBranches(activeOnly = true): Promise<void> {
    if (!auth.isAuthenticated.value) {
      return
    }

    isLoading.value = true
    try {
      const response = await api.get<ApiResponse<Branch[]>>(`/api/v1/branches?active_only=${activeOnly}`)
      branches.value = response.data || []

      // Determine current branch
      if (typeof window !== 'undefined') {
        const storedBranchId = localStorage.getItem(BRANCH_STORAGE_KEY)
        if (storedBranchId) {
          const matched = activeBranches.value.find(b => b.id === storedBranchId)
          if (matched) {
            currentBranch.value = matched
            return
          }
        }
      }

      // Fallback to main branch or first active branch
      if (mainBranch.value) {
        currentBranch.value = mainBranch.value
        if (typeof window !== 'undefined') {
          localStorage.setItem(BRANCH_STORAGE_KEY, mainBranch.value.id)
        }
      } else if (activeBranches.value.length > 0) {
        currentBranch.value = activeBranches.value[0]
        if (typeof window !== 'undefined') {
          localStorage.setItem(BRANCH_STORAGE_KEY, activeBranches.value[0].id)
        }
      } else {
        currentBranch.value = null
      }
    } catch (error) {
      console.error('Failed to fetch branches:', error)
    } finally {
      isLoading.value = false
    }
  }

  function switchBranch(branchId: string): void {
    const target = activeBranches.value.find(b => b.id === branchId)
    if (!target) return

    currentBranch.value = target
    if (typeof window !== 'undefined') {
      localStorage.setItem(BRANCH_STORAGE_KEY, target.id)
    }

    toast.add({
      title: t('common.success'),
      description: `${t('branch.switchedTo') || 'Switched to'}: ${target.name}`,
      color: 'success'
    })
  }

  async function createBranch(data: BranchCreate): Promise<Branch | null> {
    try {
      const response = await api.post<ApiResponse<Branch>>('/api/v1/branches', data)
      const created = response.data
      branches.value = [...branches.value, created]
      if (created.is_main || branches.value.length === 1) {
        currentBranch.value = created
        if (typeof window !== 'undefined') {
          localStorage.setItem(BRANCH_STORAGE_KEY, created.id)
        }
      }
      toast.add({
        title: t('common.success'),
        description: t('branch.toast.created') || 'Branch created successfully',
        color: 'success'
      })
      return created
    } catch (e: unknown) {
      toast.add({
        title: t('common.error'),
        description: (e as any)?.message || t('branch.toast.createError') || 'Failed to create branch',
        color: 'error'
      })
      return null
    }
  }

  async function updateBranch(branchId: string, data: BranchUpdate): Promise<Branch | null> {
    try {
      const response = await api.put<ApiResponse<Branch>>(`/api/v1/branches/${branchId}`, data)
      const updated = response.data
      branches.value = branches.value.map(b => b.id === branchId ? updated : (data.is_main ? { ...b, is_main: false } : b))
      if (currentBranch.value?.id === branchId) {
        currentBranch.value = updated
      }
      toast.add({
        title: t('common.success'),
        description: t('branch.toast.updated') || 'Branch updated successfully',
        color: 'success'
      })
      return updated
    } catch (e: unknown) {
      toast.add({
        title: t('common.error'),
        description: (e as any)?.message || t('branch.toast.updateError') || 'Failed to update branch',
        color: 'error'
      })
      return null
    }
  }

  async function deleteBranch(branchId: string): Promise<boolean> {
    try {
      await api.delete(`/api/v1/branches/${branchId}`)
      branches.value = branches.value.filter(b => b.id !== branchId)
      if (currentBranch.value?.id === branchId) {
        currentBranch.value = mainBranch.value
        if (typeof window !== 'undefined' && mainBranch.value) {
          localStorage.setItem(BRANCH_STORAGE_KEY, mainBranch.value.id)
        }
      }
      toast.add({
        title: t('common.success'),
        description: t('branch.toast.deleted') || 'Branch deleted successfully',
        color: 'success'
      })
      return true
    } catch (e: unknown) {
      toast.add({
        title: t('common.error'),
        description: (e as any)?.message || t('branch.toast.deleteError') || 'Failed to delete branch',
        color: 'error'
      })
      return false
    }
  }

  return {
    branches,
    activeBranches,
    mainBranch,
    currentBranch,
    isLoading,
    fetchBranches,
    switchBranch,
    createBranch,
    updateBranch,
    deleteBranch
  }
}

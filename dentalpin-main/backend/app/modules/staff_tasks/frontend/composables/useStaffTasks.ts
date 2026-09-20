export type TaskStatus = 'open' | 'claimed' | 'done' | 'cancelled'
export type TaskPriority = 'low' | 'normal' | 'high'

export interface StaffTask {
  id: string
  clinic_id: string
  title: string
  details?: string | null
  status: TaskStatus
  priority: TaskPriority
  assignee_id?: string | null
  assignee_name?: string | null
  created_by?: string | null
  due_date?: string | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

export interface StaffTaskCreatePayload {
  title: string
  details?: string | null
  priority: TaskPriority
  assignee_id?: string | null
  due_date?: string | null
}

export interface StaffTaskUpdatePayload {
  title?: string
  details?: string | null
  priority?: TaskPriority
  status?: TaskStatus
  assignee_id?: string | null
  due_date?: string | null
}

interface ApiOk<T> { data: T, message?: string | null }
interface ApiPaged<T> { data: T[], total: number, page: number, page_size: number }

export interface StaffTaskListFilters {
  task_status?: TaskStatus
  assignee_id?: string
  due_before?: string
  page?: number
  page_size?: number
}

export function useStaffTasks() {
  const api = useApi()

  async function list(filters: StaffTaskListFilters = {}): Promise<ApiPaged<StaffTask>> {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(filters)) {
      if (v === undefined || v === null || v === '') continue
      qs.append(k, String(v))
    }
    const url = `/api/v1/staff_tasks/${qs.toString() ? `?${qs.toString()}` : ''}`
    return await api.get<ApiPaged<StaffTask>>(url)
  }

  async function create(payload: StaffTaskCreatePayload): Promise<ApiOk<StaffTask>> {
    return await api.post<ApiOk<StaffTask>>('/api/v1/staff_tasks/', payload)
  }

  async function update(id: string, payload: StaffTaskUpdatePayload): Promise<ApiOk<StaffTask>> {
    return await api.patch<ApiOk<StaffTask>>(`/api/v1/staff_tasks/${id}`, payload)
  }

  async function remove(id: string): Promise<void> {
    await api.del(`/api/v1/staff_tasks/${id}`)
  }

  return { list, create, update, remove }
}

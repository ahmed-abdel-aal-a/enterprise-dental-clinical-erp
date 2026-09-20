/**
 * DentApex Conflict-Aware Offline Outbox Manager.
 *
 * Implements optimistic mutations, automatic background replay,
 * and robust HTTP 409 Conflict handling to prevent double-booking.
 */

import type { OutboxItem } from './useOfflineDb'

export function useOutbox() {
  const offlineDb = useOfflineDb()
  const syncing = useState<boolean>('dentapex:outbox:syncing', () => false)
  const pendingCount = useState<number>('dentapex:outbox:pendingCount', () => 0)
  const activeConflict = useState<OutboxItem | null>('dentapex:outbox:activeConflict', () => null)
  const isOfflineMode = useState<boolean>('dentapex:offlineMode', () => false)

  async function refreshPendingCount(): Promise<number> {
    if (!import.meta.client) return 0
    try {
      const items = await offlineDb.getAll<OutboxItem>('outbox')
      pendingCount.value = items.filter(i => i.status === 'pending' || i.status === 'conflict').length
      return pendingCount.value
    } catch {
      return 0
    }
  }

  async function enqueueMutation<T = any>(
    endpoint: string,
    method: 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    payload: any
  ): Promise<{ optimisticId: string; optimisticEntity: any }> {
    const optimisticId = `temp_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    const nowIso = new Date().toISOString()

    const optimisticEntity = {
      ...payload,
      id: optimisticId,
      _sync_status: 'pending',
      created_at: nowIso,
      updated_at: nowIso,
    }

    const outboxItem: OutboxItem = {
      id: optimisticId,
      endpoint,
      method,
      payload,
      created_at: nowIso,
      status: 'pending',
      retry_count: 0,
    }

    // 1. Persist mutation to Outbox
    await offlineDb.put('outbox', outboxItem)

    // 2. Optimistically update domain store
    if (endpoint.includes('/agenda/appointments')) {
      await offlineDb.put('appointments', optimisticEntity)
    } else if (endpoint.includes('/patients')) {
      await offlineDb.put('patients', optimisticEntity)
    }

    await refreshPendingCount()
    return { optimisticId, optimisticEntity }
  }

  async function checkConnection(): Promise<boolean> {
    if (!import.meta.client) return true
    try {
      const config = useRuntimeConfig()
      const baseUrl = (config.public.apiBaseUrl || '').replace(/\/$/, '')
      await $fetch(`${baseUrl}/health`, { method: 'GET', timeout: 4000 })
      isOfflineMode.value = false
      return true
    } catch {
      isOfflineMode.value = true
      return false
    }
  }

  async function syncOutbox(): Promise<{ synced: number; conflicts: number }> {
    if (!import.meta.client || syncing.value) return { synced: 0, conflicts: 0 }
    syncing.value = true

    let synced = 0
    let conflicts = 0

    try {
      const items = await offlineDb.getAll<OutboxItem>('outbox')
      const actionable = items.filter(i => i.status === 'pending')

      if (actionable.length === 0) {
        await checkConnection()
      }

      for (const item of actionable) {
        try {
          const auth = useAuth()
          const config = useRuntimeConfig()
          const baseUrl = (config.public.apiBaseUrl || '').replace(/\/$/, '')

          const res = await $fetch<any>(`${baseUrl}${item.endpoint}`, {
            method: item.method,
            body: item.payload,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${auth.accessToken.value || ''}`,
            },
          })

          // Success: replace optimistic entity with official server record
          const serverData = res?.data || res
          if (serverData && serverData.id) {
            if (item.endpoint.includes('/agenda/appointments')) {
              await offlineDb.remove('appointments', item.id)
              await offlineDb.put('appointments', { ...serverData, _sync_status: 'synced' })
            } else if (item.endpoint.includes('/patients')) {
              await offlineDb.remove('patients', item.id)
              await offlineDb.put('patients', { ...serverData, _sync_status: 'synced' })
            }
          }

          // Remove item from Outbox
          await offlineDb.remove('outbox', item.id)
          synced++
        } catch (err: any) {
          // Check for 409 Conflict (Double booking)
          const statusCode = err?.status || err?.statusCode
          if (statusCode === 409) {
            conflicts++
            const conflictDetail = err?.data?.detail || {
              code: 'TIME_SLOT_CONFLICT',
              message: 'هذا الموعد محجوز مسبقاً لمريض آخر',
            }

            item.status = 'conflict'
            item.conflict_details = conflictDetail
            await offlineDb.put('outbox', item)

            // Surface active conflict modal to user
            activeConflict.value = item
          } else {
            // Network failure: server remains unreachable, stop replay
            isOfflineMode.value = true
            break
          }
        }
      }
    } finally {
      syncing.value = false
      await refreshPendingCount()
    }

    return { synced, conflicts }
  }

  async function resolveConflict(outboxId: string, updatedPayload: any): Promise<void> {
    const item = await offlineDb.get<OutboxItem>('outbox', outboxId)
    if (!item) return

    item.payload = { ...item.payload, ...updatedPayload }
    item.status = 'pending'
    delete item.conflict_details
    await offlineDb.put('outbox', item)

    // Update optimistic appointment in local DB
    if (item.endpoint.includes('/agenda/appointments')) {
      const apt = await offlineDb.get('appointments', outboxId)
      if (apt) {
        await offlineDb.put('appointments', { ...apt, ...updatedPayload, _sync_status: 'pending' })
      }
    }

    activeConflict.value = null
    await syncOutbox()
  }

  async function cancelConflict(outboxId: string): Promise<void> {
    await offlineDb.remove('outbox', outboxId)
    await offlineDb.remove('appointments', outboxId)
    activeConflict.value = null
    await refreshPendingCount()
  }

  return {
    syncing,
    pendingCount,
    activeConflict,
    isOfflineMode,
    checkConnection,
    refreshPendingCount,
    enqueueMutation,
    syncOutbox,
    resolveConflict,
    cancelConflict,
  }
}

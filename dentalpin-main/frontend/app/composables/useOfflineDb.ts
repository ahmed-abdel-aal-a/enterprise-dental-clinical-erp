/**
 * DentApex Offline Storage Engine (Native IndexedDB Wrapper).
 *
 * Provides zero-latency client-side caching for 24/7 mobile access
 * when clinic laptop is powered off. Zero external npm dependencies.
 */

const DB_NAME = 'dentapex_offline_db'
const DB_VERSION = 1

export interface OutboxItem {
  id: string // Client-generated UUID (e.g. temp_1726768800_abc)
  endpoint: string
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  payload: any
  created_at: string
  status: 'pending' | 'syncing' | 'conflict' | 'failed'
  conflict_details?: {
    code: string
    message: string
    conflicting_appointment?: {
      id: string
      patient_name: string
      start_time: string
      end_time: string
      cabinet?: string
    }
  }
  retry_count: number
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!import.meta.client || typeof window === 'undefined' || !window.indexedDB) {
      return reject(new Error('IndexedDB not supported or running server-side'))
    }

    const req = window.indexedDB.open(DB_NAME, DB_VERSION)

    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result

      // 1. Patients store
      if (!db.objectStoreNames.contains('patients')) {
        const pStore = db.createObjectStore('patients', { keyPath: 'id' })
        pStore.createIndex('full_name', 'full_name', { unique: false })
        pStore.createIndex('phone', 'phone', { unique: false })
      }

      // 2. Appointments store
      if (!db.objectStoreNames.contains('appointments')) {
        const aStore = db.createObjectStore('appointments', { keyPath: 'id' })
        aStore.createIndex('start_time', 'start_time', { unique: false })
        aStore.createIndex('patient_id', 'patient_id', { unique: false })
        aStore.createIndex('status', 'status', { unique: false })
      }

      // 3. Treatment Catalog store
      if (!db.objectStoreNames.contains('catalog')) {
        db.createObjectStore('catalog', { keyPath: 'id' })
      }

      // 4. Invoices & Billing summary store
      if (!db.objectStoreNames.contains('invoices')) {
        db.createObjectStore('invoices', { keyPath: 'id' })
      }

      // 5. Offline Outbox queue store
      if (!db.objectStoreNames.contains('outbox')) {
        const oStore = db.createObjectStore('outbox', { keyPath: 'id' })
        oStore.createIndex('created_at', 'created_at', { unique: false })
        oStore.createIndex('status', 'status', { unique: false })
      }

      // 6. Meta metadata store (key-value)
      if (!db.objectStoreNames.contains('meta')) {
        db.createObjectStore('meta', { keyPath: 'key' })
      }
    }

    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export function useOfflineDb() {
  async function put(storeName: string, item: any): Promise<void> {
    const db = await openDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite')
      const store = tx.objectStore(storeName)
      const req = store.put(item)
      req.onsuccess = () => resolve()
      req.onerror = () => reject(req.error)
    })
  }

  async function putMany(storeName: string, items: any[]): Promise<void> {
    if (!items.length) return
    const db = await openDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite')
      const store = tx.objectStore(storeName)
      for (const it of items) {
        store.put(it)
      }
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  async function get<T = any>(storeName: string, key: string): Promise<T | null> {
    const db = await openDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly')
      const store = tx.objectStore(storeName)
      const req = store.get(key)
      req.onsuccess = () => resolve(req.result || null)
      req.onerror = () => reject(req.error)
    })
  }

  async function getAll<T = any>(storeName: string): Promise<T[]> {
    const db = await openDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly')
      const store = tx.objectStore(storeName)
      const req = store.getAll()
      req.onsuccess = () => resolve(req.result || [])
      req.onerror = () => reject(req.error)
    })
  }

  async function remove(storeName: string, key: string): Promise<void> {
    const db = await openDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite')
      const store = tx.objectStore(storeName)
      const req = store.delete(key)
      req.onsuccess = () => resolve()
      req.onerror = () => reject(req.error)
    })
  }

  async function getMeta<T = any>(key: string): Promise<T | null> {
    const row = await get<{ key: string; value: T }>('meta', key)
    return row ? row.value : null
  }

  async function setMeta<T = any>(key: string, value: T): Promise<void> {
    await put('meta', { key, value, updated_at: new Date().toISOString() })
  }

  // Specialized search helper for patients
  async function searchPatients(query: string): Promise<any[]> {
    const all = await getAll('patients')
    if (!query.trim()) return all.slice(0, 50)
    const q = query.toLowerCase().trim()
    return all.filter(p =>
      (p.full_name && p.full_name.toLowerCase().includes(q)) ||
      (p.phone && p.phone.includes(q)) ||
      (p.first_name && p.first_name.toLowerCase().includes(q)) ||
      (p.last_name && p.last_name.toLowerCase().includes(q))
    ).slice(0, 50)
  }

  // Specialized query helper for appointments in a date range
  async function getAppointmentsForRange(startDateIso: string, endDateIso: string): Promise<any[]> {
    const all = await getAll('appointments')
    const start = new Date(startDateIso).getTime()
    const end = new Date(endDateIso).getTime()
    return all.filter(a => {
      const t = new Date(a.start_time).getTime()
      return t >= start && t <= end
    }).sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  }

  return {
    put,
    putMany,
    get,
    getAll,
    remove,
    getMeta,
    setMeta,
    searchPatients,
    getAppointmentsForRange,
  }
}

/**
 * DentApex Vault Restore Engine (In-Browser AES-256-GCM Decryption).
 *
 * Downloads encrypted clinical snapshots from the private Cloudflare R2 Vault
 * via the authenticated Edge Worker Gateway, decrypts client-side using
 * the standard Web Crypto API, and hydrates IndexedDB for instant 24/7 access.
 * Zero-Knowledge: Cloudflare never sees the plaintext data.
 */

const MAGIC = new Uint8Array([0x44, 0x50, 0x41, 0x58]) // 'DPAX'

async function deriveAesKey(passphrase: string, salt: Uint8Array): Promise<CryptoKey> {
  const encoder = new TextEncoder()
  const baseKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(passphrase),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  )

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt as any,
      iterations: 100_000,
      hash: 'SHA-256',
    },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt']
  )
}

export function useVaultRestore() {
  const offlineDb = useOfflineDb()
  const auth = useAuth()
  const config = useRuntimeConfig()
  const restoring = useState<boolean>('dentapex:vault:restoring', () => false)

  async function restoreFromVault(passphrase: string, clinicId?: string): Promise<{
    success: boolean
    patients: number
    appointments: number
    catalog: number
  }> {
    if (!import.meta.client) return { success: false, patients: 0, appointments: 0, catalog: 0 }
    restoring.value = true

    try {
      const edgeWorkerUrl = (config.public.edgeWorkerUrl || '').replace(/\/$/, '')
      const token = auth.accessToken.value
      const cid = clinicId || auth.user.value?.clinic_id || ''

      const endpoint = edgeWorkerUrl
        ? `${edgeWorkerUrl}/api/edge/vault/snapshot?clinic_id=${cid}`
        : `/api/v1/vault/snapshot?encrypted=true`

      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`

      const response = await fetch(endpoint, { method: 'GET', headers })
      if (!response.ok) {
        throw new Error(`Failed to download vault snapshot (HTTP ${response.status})`)
      }

      const buffer = await response.arrayBuffer()
      const bytes = new Uint8Array(buffer)

      if (bytes.length < 36) {
        throw new Error('Corrupted or truncated vault snapshot')
      }

      // Verify Magic
      for (let i = 0; i < 4; i++) {
        if (bytes[i] !== MAGIC[i]) {
          throw new Error('Invalid DentApex Vault signature')
        }
      }

      let offset = 4
      const salt = bytes.slice(offset, offset + 16)
      offset += 16
      const iv = bytes.slice(offset, offset + 12)
      offset += 12
      const ciphertext = bytes.slice(offset)

      // Derive key and decrypt via Web Crypto API
      const key = await deriveAesKey(passphrase, salt)
      const decryptedBuffer = await crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv as any,
          additionalData: MAGIC as any,
        },
        key,
        ciphertext as any
      )

      const jsonStr = new TextDecoder('utf-8').decode(decryptedBuffer)
      const snapshot = JSON.parse(jsonStr)

      // Hydrate IndexedDB
      if (Array.isArray(snapshot.patients)) {
        await offlineDb.putMany('patients', snapshot.patients)
      }
      if (Array.isArray(snapshot.appointments)) {
        await offlineDb.putMany('appointments', snapshot.appointments)
      }
      if (Array.isArray(snapshot.catalog)) {
        await offlineDb.putMany('catalog', snapshot.catalog)
      }

      await offlineDb.setMeta('last_vault_sync', new Date().toISOString())
      await offlineDb.setMeta('vault_clinic_id', snapshot.clinic_id)

      return {
        success: true,
        patients: snapshot.patients?.length || 0,
        appointments: snapshot.appointments?.length || 0,
        catalog: snapshot.catalog?.length || 0,
      }
    } finally {
      restoring.value = false
    }
  }

  return {
    restoring,
    restoreFromVault,
  }
}

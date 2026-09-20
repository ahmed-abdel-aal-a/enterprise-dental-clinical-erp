import type { User, LoginCredentials, AuthResponse, MeResponse, ApiResponse } from '~/types'

const DEMO_USER: User = {
  id: 'demo-user-00000000-0000-0000-0000-000000000001',
  email: 'ahmed@dentapex.clinic',
  first_name: 'د. أحمد',
  last_name: 'عبد العال',
  is_active: true,
  role: 'admin',
  is_professional: true,
  created_at: '2026-01-01T00:00:00Z',
}

const ALL_PERMISSIONS = [
  '*',
  'patients.read', 'patients.write',
  'patients_clinical.medical.read', 'patients_clinical.medical.write',
  'patients_clinical.emergency.read', 'patients_clinical.emergency.write',
  'agenda.appointments.read', 'agenda.appointments.write',
  'admin.users.read', 'admin.users.write',
  'odontogram.read', 'odontogram.write',
  'odontogram.treatments.read', 'odontogram.treatments.write',
  'catalog.read', 'catalog.write', 'catalog.admin',
  'budget.read', 'budget.write', 'budget.admin', 'budget.renegotiate', 'budget.accept_in_clinic',
  'billing.read', 'billing.write', 'billing.admin',
  'notifications.templates.read', 'notifications.templates.write',
  'notifications.preferences.read', 'notifications.preferences.write',
  'notifications.logs.read', 'notifications.send', 'notifications.settings.read', 'notifications.settings.write',
  'reports.billing.read', 'reports.budgets.read', 'reports.scheduling.read',
  'media.documents.read', 'media.documents.write',
  'media.attachments.read', 'media.attachments.write',
  'treatment_plan.plans.read', 'treatment_plan.plans.write', 'treatment_plan.plans.confirm', 'treatment_plan.plans.close', 'treatment_plan.plans.reactivate',
  'clinical_notes.notes.read', 'clinical_notes.notes.write',
  'agents.view', 'agents.supervise', 'agents.configure', 'agents.manage',
  'admin.clinic.read', 'admin.clinic.write',
  'migration_import.job.read', 'migration_import.job.write', 'migration_import.job.execute', 'migration_import.binary.write',
  'payments.record.read', 'payments.record.write', 'payments.record.refund', 'payments.reports.read',
  'verifactu.settings.read', 'verifactu.settings.configure', 'verifactu.queue.manage', 'verifactu.records.read', 'verifactu.environment.promote',
  'india_gst.settings.read', 'india_gst.settings.configure', 'india_gst.catalog.manage', 'india_gst.reports.read',
  'recalls.read', 'recalls.write', 'recalls.delete',
  'whatsapp_kapso.settings.read', 'whatsapp_kapso.settings.write',
  'schedules.clinic_hours.read', 'schedules.clinic_hours.write', 'schedules.professional.read', 'schedules.professional.write',
  'schedules.professional.own.read', 'schedules.professional.own.write',
  'periodontogram.read', 'periodontogram.write',
  'copilot.chat', 'copilot.history.read', 'copilot.history.read_all', 'copilot.supervise', 'copilot.configure',
  'accounting_export.export.read', 'accounting_export.export.run',
  'lab_orders.read', 'lab_orders.write',
  'patient_relationships.read', 'patient_relationships.write',
  'expenses.read', 'expenses.write',
  'contacts.read', 'contacts.write',
  'staff_tasks.read', 'staff_tasks.write',
  'inventory.read', 'inventory.write',
  'treatment_consumables.read', 'treatment_consumables.write',
  'activity_journal.read',
  'medication_catalog.read', 'medication_catalog.write'
]

// Client-only module-level dedupe slot for the in-flight refresh promise.
let clientRefreshInFlight: Promise<boolean> | null = null

export function useAuth() {
  const config = useRuntimeConfig()
  const router = useRouter()

  const isSimulator = computed(() => Boolean(config.public.demoMode))

  // Use different API URL for server (Docker internal) vs client (browser)
  const apiBaseUrl = computed(() =>
    import.meta.server ? config.apiBaseUrlServer : config.public.apiBaseUrl
  )

  // State: In enterprise edition, starts unauthenticated (null)
  const user = useState<User | null>('auth:user', () => null)
  const permissions = useState<string[]>('auth:permissions', () => [])

  // Isolated cookie lifetime: 30 days matching backend REFRESH_TOKEN_EXPIRE_DAYS=30.
  const isHttps = typeof window !== 'undefined' ? window.location.protocol === 'https:' : false
  const accessToken = useCookie<string | null>('dentapex_ent_access_token', {
    maxAge: 60 * 60 * 24 * 30, // 30 days
    secure: isHttps,
    sameSite: 'lax',
    default: () => null,
    encode: (val: any) => String(val ?? ''),
    decode: (val: string) => val
  })
  const refreshToken = useCookie<string | null>('dentapex_ent_refresh_token', {
    maxAge: 60 * 60 * 24 * 30, // 30 days
    secure: isHttps,
    sameSite: 'lax',
    default: () => null,
    encode: (val: any) => String(val ?? ''),
    decode: (val: string) => val
  })

  function syncTokensToStorage(access: string | null, refresh: string | null) {
    if (typeof window === 'undefined' || !window.localStorage) return
    try {
      if (access) {
        localStorage.setItem('dentapex_ent_access_token', access)
      } else {
        localStorage.removeItem('dentapex_ent_access_token')
      }
      if (refresh) {
        localStorage.setItem('dentapex_ent_refresh_token', refresh)
      } else {
        localStorage.removeItem('dentapex_ent_refresh_token')
      }
    } catch {
      // Ignore quota / private mode storage errors
    }
  }

  // Computed
  const isAuthenticated = computed(() => {
    if (isSimulator.value) return true
    return !!accessToken.value && !!user.value
  })

  // Actions
  async function login(credentials: LoginCredentials): Promise<void> {
    if (isSimulator.value) {
      user.value = DEMO_USER
      permissions.value = ALL_PERMISSIONS
      accessToken.value = 'dentapex-demo-token-2026'
      if (import.meta.client) router.push('/')
      return
    }

    // OAuth2PasswordRequestForm expects form data with 'username' field
    const formData = new URLSearchParams()
    formData.append('username', credentials.email)
    formData.append('password', credentials.password)

    const response = await $fetch<AuthResponse>('/api/v1/auth/login', {
      baseURL: apiBaseUrl.value,
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    await applyTokens(response.access_token, response.refresh_token)
  }

  /** Store a token pair obtained out-of-band (e.g. invite set-password) and load the user. */
  async function applyTokens(access: string, refresh: string): Promise<void> {
    accessToken.value = access
    refreshToken.value = refresh
    syncTokensToStorage(access, refresh)
    await fetchUser()
  }

  async function logout(): Promise<void> {
    if (isSimulator.value) {
      if (import.meta.client) {
        localStorage.removeItem('dentapex_patients')
        localStorage.removeItem('dentapex_appointments')
        window.location.reload()
      }
      return
    }

    accessToken.value = null
    refreshToken.value = null
    syncTokensToStorage(null, null)
    user.value = null
    permissions.value = []
    if (import.meta.client) {
      await router.push('/login')
    }
  }

  // Dedupe concurrent refreshes. Without this, a page that fires N
  // parallel requests on an expired access token triggers N refresh
  // calls — all but one race past the rate limiter and trip 429,
  // which then logs the user out. Sharing one in-flight promise keeps
  // the refresh single-shot per session. Stored in a client-only
  // module-level slot (see top of file) — putting a Promise into
  // useState() breaks SSR payload serialization.
  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) {
      return false
    }

    if (import.meta.client && clientRefreshInFlight) {
      return clientRefreshInFlight
    }

    const run = (async (): Promise<boolean> => {
      try {
        const response = await $fetch<AuthResponse>('/api/v1/auth/refresh', {
          baseURL: apiBaseUrl.value,
          method: 'POST',
          body: { refresh_token: refreshToken.value }
        })

        accessToken.value = response.access_token
        refreshToken.value = response.refresh_token
        syncTokensToStorage(response.access_token, response.refresh_token)
        user.value = response.user

        // /auth/refresh returns user but not the expanded permissions list,
        // so pull /me with the new token. Without this, callers that wake
        // up from an expired access token end up with empty permissions
        // and the sidebar/home strip every permission-gated entry.
        const me = await $fetch<ApiResponse<MeResponse>>('/api/v1/auth/me', {
          baseURL: apiBaseUrl.value,
          headers: { Authorization: `Bearer ${response.access_token}` }
        })
        user.value = me.data.user
        permissions.value = me.data.permissions
        return true
      } catch {
        await logout()
        return false
      }
    })()

    if (import.meta.client) {
      clientRefreshInFlight = run
    }
    try {
      return await run
    } finally {
      if (import.meta.client) {
        clientRefreshInFlight = null
      }
    }
  }

  async function fetchUser(): Promise<void> {
    if (isSimulator.value) {
      user.value = DEMO_USER
      permissions.value = ALL_PERMISSIONS
      return
    }

    if (!accessToken.value) {
      return
    }

    try {
      const response = await $fetch<ApiResponse<MeResponse>>('/api/v1/auth/me', {
        baseURL: apiBaseUrl.value,
        headers: {
          Authorization: `Bearer ${accessToken.value}`
        }
      })
      user.value = response.data.user
      permissions.value = response.data.permissions
    } catch (error: unknown) {
      const fetchError = error as { statusCode?: number }
      // Only try refresh on 401 (expired token), not on other errors
      if (fetchError.statusCode === 401) {
        const refreshed = await refresh()
        if (!refreshed) {
          await logout()
        }
      } else {
        // Log the error but don't logout on non-401 errors
        console.error('Failed to fetch user:', error)
        throw error
      }
    }
  }

  // Initialize user if token exists (works on both server and client).
  // Must never throw: the global auth middleware awaits this on SSR, and
  // an unhandled rejection there crashes the response so the user sees
  // neither the page nor a redirect to /login. On any failure, clear
  // auth state so the middleware can route to /login.
  async function init(): Promise<void> {
    if (isSimulator.value) {
      if (!user.value) user.value = DEMO_USER
      if (!permissions.value || permissions.value.length === 0) permissions.value = ALL_PERMISSIONS
      if (!accessToken.value) accessToken.value = 'dentapex-demo-token-2026'
      return
    }

    try {
      // Client-side session recovery from localStorage if browser cleared cookies on exit
      if (import.meta.client && typeof window !== 'undefined' && window.localStorage) {
        try {
          if (!accessToken.value) {
            const storedAccess = localStorage.getItem('dentapex_ent_access_token')
            if (storedAccess) accessToken.value = storedAccess
          }
          if (!refreshToken.value) {
            const storedRefresh = localStorage.getItem('dentapex_ent_refresh_token')
            if (storedRefresh) refreshToken.value = storedRefresh
          }
        } catch {
          // Ignore localStorage access errors
        }
      }

      if (accessToken.value && !user.value) {
        await fetchUser()
      } else if (!accessToken.value && refreshToken.value) {
        // Access cookie gone but refresh still valid — recover session.
        await refresh()
      }
    } catch {
      accessToken.value = null
      refreshToken.value = null
      syncTokensToStorage(null, null)
      user.value = null
      permissions.value = []
    }
  }

  return {
    user: readonly(user),
    permissions: readonly(permissions),
    accessToken: readonly(accessToken),
    isAuthenticated,
    login,
    applyTokens,
    logout,
    refresh,
    fetchUser,
    init
  }
}

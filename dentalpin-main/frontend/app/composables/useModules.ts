/**
 * Backend-driven module + navigation registry.
 *
 * Fetches ``GET /api/v1/modules/-/active`` once per session and caches
 * the result in :func:`useState`. The sidebar consumes
 * ``navigationItems`` — entries are permission-filtered on the server
 * and re-translated client-side via i18n. ``ensureLoaded`` is
 * idempotent so guards / layouts can call it without coordinating.
 *
 * If the fetch fails the sidebar shows only the host shell entries
 * (dashboard + settings); module-owned items are gated on the backend
 * response.
 */

import type { ActiveModule, ApiResponse, NavigationItem } from '~/types'

// Host shell nav: dashboard + settings belong to the host app, not to
// any module. Always rendered, even when the modules endpoint fails.
const HOST_NAV: NavigationItem[] = [
  {
    label: 'nav.dashboard',
    icon: 'i-lucide-home',
    to: '/',
    order: 0
  },
  {
    label: 'nav.settings',
    icon: 'i-lucide-settings',
    to: '/settings',
    order: 900
  }
]

export const DEMO_MODULES: ActiveModule[] = [
  {
    name: 'patients',
    version: '0.4.0',
    category: 'official',
    summary: 'إدارة المرضى والسجلات الطبية',
    permissions: ['patients.read', 'patients.write'],
    navigation: [
      {
        label: 'nav.patients',
        icon: 'i-lucide-users',
        to: '/patients',
        permission: 'patients.read',
        order: 10
      }
    ]
  },
  {
    name: 'agenda',
    version: '0.4.0',
    category: 'official',
    summary: 'الأجندة والمواعيد وجدول العيادات',
    permissions: ['agenda.appointments.read', 'agenda.appointments.write'],
    navigation: [
      {
        label: 'nav.appointments',
        icon: 'i-lucide-calendar',
        to: '/appointments',
        permission: 'agenda.appointments.read',
        order: 20
      }
    ]
  },
  {
    name: 'treatment_plan',
    version: '0.4.0',
    category: 'official',
    summary: 'خطط العلاج والمراحل السريرية',
    permissions: ['treatment_plan.plans.read', 'treatment_plan.plans.write'],
    navigation: [
      {
        label: 'nav.treatmentPlans',
        icon: 'i-lucide-clipboard-list',
        to: '/treatment-plans',
        permission: 'treatment_plan.plans.read',
        order: 30
      }
    ]
  },
  {
    name: 'budget',
    version: '0.4.0',
    category: 'official',
    summary: 'عروض الأسعار والخطط المالية',
    permissions: ['budget.read', 'budget.write'],
    navigation: [
      {
        label: 'nav.budgets',
        icon: 'i-lucide-file-text',
        to: '/budgets',
        permission: 'budget.read',
        order: 40
      }
    ]
  },
  {
    name: 'billing',
    version: '0.4.0',
    category: 'official',
    summary: 'الفواتير والحسابات وسندات القبض',
    permissions: ['billing.read', 'billing.write'],
    navigation: [
      {
        label: 'nav.invoices',
        icon: 'i-lucide-receipt',
        to: '/invoices',
        permission: 'billing.read',
        order: 50
      }
    ]
  },
  {
    name: 'payments',
    version: '0.4.0',
    category: 'official',
    summary: 'المدفوعات والمتحصلات',
    permissions: ['payments.record.read', 'payments.record.write'],
    navigation: [
      {
        label: 'payments.nav.payments',
        icon: 'i-lucide-wallet',
        to: '/payments',
        permission: 'payments.record.read',
        order: 55
      }
    ]
  },
  {
    name: 'reports',
    version: '0.4.0',
    category: 'official',
    summary: 'التقارير والإحصائيات والرسوم البيانية',
    permissions: ['reports.billing.read'],
    navigation: [
      {
        label: 'nav.reports',
        icon: 'i-lucide-bar-chart-3',
        to: '/reports',
        permission: 'reports.billing.read',
        order: 60
      }
    ]
  },
  {
    name: 'copilot',
    version: '0.4.0',
    category: 'official',
    summary: 'المساعد الذكي السريري والتشخيصي',
    permissions: ['copilot.chat'],
    navigation: [
      {
        label: 'nav.copilot',
        icon: 'i-lucide-sparkles',
        to: '/copilot',
        permission: 'copilot.chat',
        order: 90
      }
    ]
  },
  {
    name: 'inventory',
    version: '0.4.0',
    category: 'official',
    summary: 'المخزون والمستلزمات الطبية',
    permissions: ['inventory.read', 'inventory.write'],
    navigation: [
      {
        label: 'nav.inventory',
        icon: 'i-lucide-package',
        to: '/inventory',
        permission: 'inventory.read',
        order: 93
      }
    ]
  },
  {
    name: 'lab_orders',
    version: '0.4.0',
    category: 'official',
    summary: 'طلبات معامل الأسنان والتركيبات',
    permissions: ['lab_orders.read', 'lab_orders.write'],
    navigation: [
      {
        label: 'lab_orders.nav',
        icon: 'i-lucide-flask-conical',
        to: '/lab-orders',
        permission: 'lab_orders.read',
        order: 95
      }
    ]
  },
  {
    name: 'contacts',
    version: '0.4.0',
    category: 'official',
    summary: 'جهات الاتصال والموردين',
    permissions: ['contacts.read', 'contacts.write'],
    navigation: [
      {
        label: 'contacts.nav',
        icon: 'i-lucide-contact',
        to: '/contacts',
        permission: 'contacts.read',
        order: 97
      }
    ]
  },
  {
    name: 'expenses',
    version: '0.4.0',
    category: 'official',
    summary: 'المصروفات التشغيلية للعيادة',
    permissions: ['expenses.read', 'expenses.write'],
    navigation: [
      {
        label: 'expenses.nav',
        icon: 'i-lucide-trending-down',
        to: '/expenses',
        permission: 'expenses.read',
        order: 98
      }
    ]
  },
  {
    name: 'staff_tasks',
    version: '0.4.0',
    category: 'official',
    summary: 'مهام فريق العمل والتمريض',
    permissions: ['staff_tasks.read', 'staff_tasks.write'],
    navigation: [
      {
        label: 'staff_tasks.nav',
        icon: 'i-lucide-check-square',
        to: '/tasks',
        permission: 'staff_tasks.read',
        order: 99
      }
    ]
  }
]

/** Context-free read of the active-module list (only ``useState``). */
export function useActiveModulesState() {
  return useState<ActiveModule[] | null>('modules:active', () => DEMO_MODULES)
}

export function useModules() {
  const { t } = useI18n()
  const { can } = usePermissions()
  const auth = useAuth()
  const api = useApi()
  const config = useRuntimeConfig()

  const active = useActiveModulesState()
  const loading = useState<boolean>('modules:active:loading', () => false)
  const error = useState<string | null>('modules:active:error', () => null)
  const lastLoadedAt = useState<number>('modules:active:at', () => 0)

  function translateLabel(key: string): string {
    const translated = t(key)
    if (translated && translated !== key) return translated
    const fallbacks: Record<string, string> = {
      'nav.patients': 'المرضى',
      'nav.appointments': 'الأجندة والمواعيد',
      'nav.treatmentPlans': 'خطط العلاج',
      'nav.budgets': 'عروض الأسعار',
      'nav.invoices': 'الفواتير والحسابات',
      'payments.nav.payments': 'المدفوعات',
      'nav.reports': 'التقارير والإحصائيات',
      'nav.copilot': 'المساعد الذكي (AI)',
      'nav.inventory': 'المخزون والمستلزمات',
      'lab_orders.nav': 'طلبات المعامل',
      'contacts.nav': 'الموردون والشركاء',
      'expenses.nav': 'المصروفات',
      'staff_tasks.nav': 'مهام العمل'
    }
    return fallbacks[key] || key
  }

  async function ensureLoaded(force = false): Promise<void> {
    if (config.public.demoMode || !config.public.apiBaseUrl) {
      active.value = DEMO_MODULES
      return
    }

    if (!auth.accessToken.value) return
    if (loading.value) return

    const age = Date.now() - lastLoadedAt.value
    const FRESH_MS = 60_000 // 1 min — cheap enough to refetch often
    if (!force && active.value !== null && age < FRESH_MS) return

    loading.value = true
    error.value = null
    try {
      const response = await api.get<ApiResponse<ActiveModule[]>>(
        '/api/v1/modules/-/active'
      )
      active.value = response.data
      lastLoadedAt.value = Date.now()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load modules'
      console.warn('useModules: backend fetch failed, using demo modules —', error.value)
      active.value = DEMO_MODULES
    } finally {
      loading.value = false
    }
  }

  const modules = computed(() => {
    if (!active.value) return []
    return active.value.map(m => ({
      name: m.name,
      label: m.name,
      icon: '',
      navigation: m.navigation
    }))
  })

  const navigationItems = computed<NavigationItem[]>(() => {
    if (!auth.user.value) return []

    const moduleNav = active.value
      ? active.value.flatMap(m => m.navigation)
      : []

    return [...HOST_NAV, ...moduleNav]
      .filter(item => !item.permission || can(item.permission))
      .slice()
      .sort((a, b) => (a.order ?? 999) - (b.order ?? 999))
      .map(item => ({ ...item, label: translateLabel(item.label) }))
  })

  return {
    modules,
    navigationItems,
    active,
    loading,
    error,
    ensureLoaded
  }
}

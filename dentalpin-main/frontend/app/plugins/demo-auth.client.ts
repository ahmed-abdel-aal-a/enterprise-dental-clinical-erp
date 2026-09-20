import { defineNuxtPlugin } from '#app'
import { useDemoStore } from '~/stores/useDemoStore'

export default defineNuxtPlugin(async (nuxtApp) => {
  if (!import.meta.client) return

  const demoStore = useDemoStore()
  const auth = useAuth()
  const { currentClinic } = useClinicState()
  const route = useRoute()
  const router = useRouter()

  // 1. Initialize Demo Clinical Sandbox (Lazy loads seed JSONs)
  localStorage.setItem('dentapex_demo_mode', 'true')
  await demoStore.initDemoData()

  // 2. Set Up Auto-Login Session (Zero Friction Guest Mode)
  if (!auth.accessToken.value || !auth.user.value) {
    auth.user.value = {
      id: demoStore.currentUser.id,
      email: demoStore.currentUser.email,
      first_name: demoStore.currentUser.first_name,
      last_name: demoStore.currentUser.last_name,
      is_active: true,
      role: demoStore.currentUser.role,
      is_professional: demoStore.currentUser.is_professional,
      created_at: new Date().toISOString(),
    } as any

    auth.permissions.value = ['*']
    auth.accessToken.value = 'dentapex-demo-guest-token-2026'

    currentClinic.value = {
      id: demoStore.clinic.id,
      name: demoStore.clinic.name,
      tax_id: 'DEMO-TAX-001',
      legal_name: demoStore.clinic.name,
      phone: demoStore.clinic.phone,
      email: demoStore.clinic.email,
      address: { city: 'القاهرة', street: 'شارع التحرير' },
      timezone: 'Africa/Cairo',
      currency: 'EGP',
      settings: { slot_duration_min: 15 },
      cabinets: [
        { id: 'cab-1', name: 'العيادة 1 (الكرسي الرئيسي)', display_order: 1 },
        { id: 'cab-2', name: 'العيادة 2 (كرسي علاج الجذور)', display_order: 2 },
      ],
    } as any
  }

  // 3. Bypass Login Screen: If landing on /login, redirect straight to /
  if (route.path === '/login') {
    router.replace('/')
  }
})

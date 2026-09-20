export default defineNuxtRouteMiddleware(async (to) => {
  const config = useRuntimeConfig()
  const isSimulator = config.public.demoMode || !config.public.apiBaseUrl
  if (isSimulator) {
    if (to.path === '/login') return navigateTo('/')
    return
  }

  const auth = useAuth()

  // Initialize auth state
  await auth.init()

  // Public routes that don't require authentication
  const publicRoutes = ['/login']
  const isPublicRoute = publicRoutes.some(route => to.path.startsWith(route))

  if (!auth.isAuthenticated.value && !isPublicRoute) {
    // Redirect to login
    return navigateTo('/login')
  }

  if (auth.isAuthenticated.value && to.path === '/login') {
    // Already authenticated, redirect to home
    return navigateTo('/')
  }
})

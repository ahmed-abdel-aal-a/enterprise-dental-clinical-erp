import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin((nuxtApp) => {
  if (!import.meta.client) return

  nuxtApp.vueApp.config.errorHandler = (err: any, instance: any, info: string) => {
    console.error('=== VUE_ERROR_CAPTURE ===')
    console.error('Message:', err?.message)
    console.error('Stack:', err?.stack)
    console.error('Component Name:', instance?.$options?.name || instance?.$options?.__name || instance?.type?.name || instance?.type?.__name)
    console.error('Lifecycle Info:', info)
  }

  nuxtApp.hook('app:error', (err: any) => {
    console.error('=== NUXT_APP_ERROR ===')
    console.error('Message:', err?.message)
    console.error('Stack:', err?.stack)
  })

  nuxtApp.hook('vue:error', (err: any, instance: any, info: string) => {
    console.error('=== VUE_HOOK_ERROR ===')
    console.error('Message:', err?.message)
    console.error('Stack:', err?.stack)
    console.error('Component Name:', instance?.$options?.name || instance?.$options?.__name || instance?.type?.name || instance?.type?.__name)
  })
})

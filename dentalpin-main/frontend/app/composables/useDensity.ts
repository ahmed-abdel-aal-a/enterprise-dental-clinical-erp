/**
 * useDensity — global UI density toggle (comfortable | compact).
 *
 * Persists in a cookie so the server can pick the right value during SSR
 * and avoid a comfortable→compact flash for users on compact mode.
 * Applies as a class on <html>.
 * Forced to 'comfortable' on viewports < 1024 px to keep tap targets ≥ 44 px.
 *
 * docs/technical/design-system.md §5
 */
import { STORAGE_KEYS } from '~/constants/storage'

export type Density = 'comfortable' | 'compact'

export function useDensity() {
  const cookie = useCookie<Density>(STORAGE_KEYS.DENSITY, {
    default: () => 'comfortable',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 365,
    encode: (val: any) => String(val ?? 'comfortable'),
    decode: (val: string) => (val === 'compact' ? 'compact' : 'comfortable')
  })

  const density = useState<Density>('ui:density', () => cookie.value ?? 'comfortable')

  // Bind the class to <html> on both server and client so SSR ships the
  // right density and there is no FOUC for compact-mode users.
  useHead({
    htmlAttrs: { class: () => `density-${density.value}` }
  })

  function applyToHtml(value: Density) {
    if (!import.meta.client) return
    const html = document.documentElement
    html.classList.remove('density-comfortable', 'density-compact')
    html.classList.add(`density-${value}`)
  }

  function setDensity(value: Density) {
    density.value = value
    cookie.value = value
    if (import.meta.client) applyToHtml(value)
  }

  function toggle() {
    setDensity(density.value === 'comfortable' ? 'compact' : 'comfortable')
  }

  // Narrow viewports get forced to comfortable so tap targets stay ≥ 44 px.
  // SSR cannot know viewport width, so this only runs on the client; the
  // cookie still seeds the initial render so no flash happens for desktop users.
  function init() {
    if (!import.meta.client) return
    const narrow = window.matchMedia('(max-width: 1023px)').matches
    const initial: Density = narrow ? 'comfortable' : density.value
    if (initial !== density.value) density.value = initial
    applyToHtml(initial)
  }

  return {
    density,
    setDensity,
    toggle,
    init
  }
}

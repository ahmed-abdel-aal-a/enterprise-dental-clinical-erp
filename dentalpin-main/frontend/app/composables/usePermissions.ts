import { PERMISSIONS } from '~/config/permissions'

export function usePermissions() {
  const auth = useAuth()
  const permissions = computed<readonly string[]>(() => auth.permissions.value ?? [])

  // Layers baked into this build vs modules the backend reports as
  // installed. `/me` grants permissions for every *registered* module
  // (installed or not), so gate here: a baked layer whose module isn't
  // active contributes no permission → its pages/slots/settings hide.
  // Unknown until the active list loads (null) → no gate.
  const builtLayers = new Set(useRuntimeConfig().public.moduleLayers as string[])
  const active = useActiveModulesState()

  function moduleActive(permission: string): boolean {
    const ns = permission.split('.')[0] ?? ''
    if (!builtLayers.has(ns) || !active.value) return true
    return active.value.some(m => m.name === ns)
  }

  function can(permission: string): boolean {
    if (permissions.value.includes('*')) return true
    return moduleActive(permission) && permissions.value.includes(permission)
  }

  function canAny(perms: string[]): boolean {
    if (permissions.value.includes('*')) return true
    return perms.some(can)
  }

  function canAll(perms: string[]): boolean {
    if (permissions.value.includes('*')) return true
    return perms.every(can)
  }

  const isAdmin = computed(() => permissions.value.includes('*') || can(PERMISSIONS.users.write))

  return {
    permissions: readonly(permissions),
    can,
    canAny,
    canAll,
    isAdmin
  }
}

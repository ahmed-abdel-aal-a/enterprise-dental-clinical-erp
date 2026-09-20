import { mountSuspended } from '@nuxt/test-utils/runtime'
import { beforeEach, describe, expect, it } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'

async function runInSetup<T>(fn: () => T): Promise<T> {
  let captured!: T
  await mountSuspended(defineComponent({
    setup() {
      captured = fn()
      return () => h('div')
    }
  }))
  return captured
}

const clinic = (onboarding: Record<string, unknown> = {}) => ({
  id: 'c1', name: 'Clinic', tax_id: 'B1', timezone: 'UTC', currency: 'EUR',
  settings: { onboarding }, cabinets: [], created_at: '', updated_at: ''
})

describe('useOnboarding', () => {
  beforeEach(async () => {
    const { registerGettingStartedRule, unregisterGettingStartedRule } = await import('~/composables/useSettingsRegistry')
    for (const id of ['a', 'b', 'c', 'opt']) unregisterGettingStartedRule(id)
    registerGettingStartedRule({ id: 'b', labelKey: 'b', to: '/b', order: 20, when: () => true })
    registerGettingStartedRule({ id: 'a', labelKey: 'a', to: '/a', order: 10, when: () => false })
    registerGettingStartedRule({ id: 'opt', labelKey: 'opt', to: '/opt', order: 5, optional: true, when: () => true })
    registerGettingStartedRule({ id: 'c', labelKey: 'c', to: '/c', order: 30, when: () => true })
  })

  it('orders rules, separates optional ones and computes progress from required only', async () => {
    const onboarding = await runInSetup(() => {
      useState('auth:permissions', () => ['admin.clinic.write'])
      useState('clinic:current', () => clinic())
      return useOnboarding()
    })
    expect(onboarding.required.value.map(s => s.id)).toEqual(['a', 'b', 'c'])
    expect(onboarding.optional.value.map(s => s.id)).toEqual(['opt'])
    expect(onboarding.progress.value).toEqual({ done: 1, total: 3 })
    expect(onboarding.pendingRequired.value.map(s => s.id)).toEqual(['b', 'c'])
    expect(onboarding.isComplete.value).toBe(false)
  })

  it('treats server-side skipped rules as done', async () => {
    const onboarding = await runInSetup(() => {
      useState('auth:permissions', () => ['admin.clinic.write'])
      return useOnboarding()
    })
    // useClinic() resets the clinic while unauthenticated — set it afterwards.
    useState('clinic:current').value = clinic({ skipped: { b: '2026-01-01', c: '2026-01-01' } })
    await nextTick()
    expect(onboarding.progress.value).toEqual({ done: 3, total: 3 })
    // completion is only trusted once rule data has been loaded
    expect(onboarding.isComplete.value).toBe(false)
    await onboarding.refresh(true)
    expect(onboarding.isComplete.value).toBe(true)
    expect(onboarding.isDismissed.value).toBe(false)
  })

  it('is dismissed when the clinic recorded a dismissal or completion', async () => {
    const onboarding = await runInSetup(() => {
      useState('auth:permissions', () => ['admin.clinic.write'])
      return useOnboarding()
    })
    useState('clinic:current').value = clinic({ dismissed_at: '2026-01-01T00:00:00Z' })
    await nextTick()
    expect(onboarding.isDismissed.value).toBe(true)
  })

  it('builds guided-mode routes with the onboarding query flag', async () => {
    const onboarding = await runInSetup(() => {
      useState('auth:permissions', () => ['admin.clinic.write'])
      useState('clinic:current', () => clinic())
      return useOnboarding()
    })
    const b = onboarding.required.value.find(s => s.id === 'b')!
    expect(onboarding.stepRoute(b)).toBe('/b?onboarding=b')
    expect(onboarding.stepRoute({ ...b, to: '/x?tab=1' })).toBe('/x?tab=1&onboarding=b')
  })
})

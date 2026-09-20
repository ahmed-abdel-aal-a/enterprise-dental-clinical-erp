import { STORAGE_KEYS } from '~/constants/storage'
import type { Composer } from 'vue-i18n'
import type { CodeLang } from '~/types'
import { SUPPORTED_LOCALES } from '~/constants/languages'

export default defineNuxtPlugin(async (nuxtApp) => {
  const i18n = nuxtApp.$i18n as Composer

  const savedLocale = localStorage.getItem(STORAGE_KEYS.LOCALE) as CodeLang

  // The `dentalpin_locale` cookie (written by setLocale, read during SSR —
  // see the i18n block in nuxt.config.ts) is the authoritative store since
  // #235. localStorage is kept as a fallback: pre-cookie users get their
  // saved language restored here, and setLocale then writes the cookie so
  // the next server render already uses it.
  if (savedLocale && SUPPORTED_LOCALES.includes(savedLocale) && savedLocale !== i18n.locale.value) {
    await i18n.setLocale(savedLocale)
  }
})

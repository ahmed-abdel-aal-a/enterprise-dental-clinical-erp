<script setup lang="ts">
import { fr, es, en, pt, de, hu, pl, it, ar } from '@nuxt/ui/locale'

const { t, locale } = useI18n()

// دعم لغة الواجهة العربية لمكونات Nuxt UI
const nuxtUILocales: Record<string, any> = { ar, en, fr, es, pt, de, hu, pl, it, ta: en }
const nuxtUILocale = computed(() => nuxtUILocales[locale.value] || ar || en)

useHead(() => ({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: locale.value,
    dir: locale.value === 'ar' ? 'rtl' : 'ltr'
  }
}))

useSeoMeta({
  title: 'DentApex - النسخة العربية الذكية',
  description: t('app.tagline')
})
</script>

<template>
  <UApp :locale="nuxtUILocale">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>

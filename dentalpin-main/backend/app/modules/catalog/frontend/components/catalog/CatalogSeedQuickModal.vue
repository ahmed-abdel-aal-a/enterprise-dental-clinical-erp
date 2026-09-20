<script setup lang="ts">
/**
 * Onboarding mini-modal: load the stock catalog (VAT types, categories,
 * reference treatments) without leaving the dashboard. Idempotent on the
 * server. Emits `saved` on success; "create my own" hands off to the
 * catalog page instead.
 */
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', v: boolean): void, (e: 'saved'): void }>()

const { t } = useI18n()
const catalog = useCatalog()

const isOpen = computed({
  get: () => props.open,
  set: (v: boolean) => emit('update:open', v)
})
const isSeeding = ref(false)

async function load() {
  isSeeding.value = true
  const ok = await catalog.seedDefaults()
  isSeeding.value = false
  if (ok) {
    emit('saved')
    isOpen.value = false
  }
}

function createOwn() {
  isOpen.value = false
  navigateTo('/settings/catalog')
}
</script>

<template>
  <UModal v-model:open="isOpen">
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-list-checks"
              class="w-5 h-5 text-primary-accent"
            />
            <div>
              <h3 class="font-semibold text-default">
                {{ t('catalog.onboarding.label') }}
              </h3>
              <p class="text-caption text-muted">
                {{ t('catalog.onboarding.description') }}
              </p>
            </div>
          </div>
        </template>

        <p class="text-sm text-muted">
          {{ t('catalog.loadDefaultsHint') }}
        </p>

        <div class="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-6">
          <UButton
            variant="ghost"
            icon="i-lucide-pencil"
            class="min-h-11 sm:min-h-0"
            @click="createOwn"
          >
            {{ t('catalog.onboarding.createOwn') }}
          </UButton>
          <UButton
            icon="i-lucide-download"
            :loading="isSeeding"
            class="min-h-11 sm:min-h-0"
            @click="load"
          >
            {{ t('catalog.loadDefaults') }}
          </UButton>
        </div>
      </UCard>
    </template>
  </UModal>
</template>

<script setup lang="ts">
// Modal wrapper for Copilot settings (Task 03 §2.4)
// Allows opening the Copilot Settings Panel within an interactive modal dialog.
import CopilotSettingsPanel from './CopilotSettingsPanel.vue'

const props = defineProps<{
  open?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const isOpen = computed({
  get: () => props.open ?? false,
  set: (val: boolean) => emit('update:open', val)
})

const { t } = useI18n()
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :title="t('copilot.settings.title')"
    :description="t('copilot.settings.description')"
    class="sm:max-w-3xl"
  >
    <template #body>
      <div class="max-h-[80vh] overflow-y-auto p-1">
        <CopilotSettingsPanel />
      </div>
    </template>
  </UModal>
</template>

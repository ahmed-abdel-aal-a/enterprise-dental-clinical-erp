<script setup lang="ts">
export interface SlotResult {
  start: string
  end?: string | null
  minutes?: number
}

defineProps<{ slots: SlotResult[] }>()
const { t } = useI18n()
const { time } = useCopilotFormat()

function duration(min?: number): string {
  if (!min || min <= 0) return ''
  const h = Math.floor(min / 60)
  const m = min % 60
  return [h ? `${h}h` : '', m ? `${m}min` : ''].filter(Boolean).join(' ')
}
</script>

<template>
  <div class="rounded-lg border border-default bg-elevated p-3">
    <p class="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted">
      <UIcon name="i-lucide-clock" />
      {{ t('copilot.card.freeSlots') }}
    </p>
    <ul class="space-y-1">
      <li
        v-for="(s, i) in slots"
        :key="i"
        class="flex items-center gap-2 text-sm"
      >
        <span class="font-medium tabular-nums">
          {{ time(s.start) }}<template v-if="s.end">–{{ time(s.end) }}</template>
        </span>
        <span
          v-if="duration(s.minutes)"
          class="text-xs text-muted"
        >
          {{ duration(s.minutes) }}
        </span>
      </li>
    </ul>
  </div>
</template>

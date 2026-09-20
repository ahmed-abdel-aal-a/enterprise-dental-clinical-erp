<script setup lang="ts">
/**
 * SegmentedControl — pill-style segmented buttons (view-mode toggles, tabs).
 *
 * Option shape: { value, label, icon?, badge?, badgeColor? }. The active
 * segment gets a white surface lift on a muted track. Optional badges
 * surface contextual counts/values ("3", "Debe 320 €") next to the label
 * without changing the active state.
 */
type BadgeColor = 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info'

interface Option {
  value: string
  label: string
  icon?: string
  badge?: string | number
  badgeColor?: BadgeColor
}

interface Props {
  modelValue: string
  options: Option[]
  size?: 'sm' | 'md'
  /**
   * When true, the bar grows to fill the parent's width and each option
   * stretches to equal share. Used for sub-nav pill-bars where modes
   * compete for the full container width (Clínica, Administración).
   */
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'sm',
  fullWidth: false
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const padding = computed(() => props.size === 'sm' ? 'px-3 py-1.5' : 'px-4 py-2')
</script>

<template>
  <div
    class="items-center gap-0.5 p-0.5 bg-surface-muted rounded-token-md overflow-x-auto"
    :class="fullWidth ? 'flex w-full' : 'inline-flex'"
    role="tablist"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="tab"
      :aria-selected="modelValue === opt.value"
      class="inline-flex items-center justify-center gap-1.5 text-ui rounded-token-sm transition-colors whitespace-nowrap"
      :class="[
        padding,
        fullWidth ? 'flex-1' : '',
        modelValue === opt.value
          ? 'bg-surface text-default shadow-token-xs'
          : 'text-muted hover:text-default'
      ]"
      @click="$emit('update:modelValue', opt.value)"
    >
      <UIcon
        v-if="opt.icon"
        :name="opt.icon"
        class="w-4 h-4 shrink-0"
      />
      <span>{{ opt.label }}</span>
      <UBadge
        v-if="opt.badge != null && opt.badge !== ''"
        :color="opt.badgeColor ?? 'neutral'"
        variant="subtle"
        size="xs"
        class="tnum"
      >
        {{ opt.badge }}
      </UBadge>
    </button>
  </div>
</template>

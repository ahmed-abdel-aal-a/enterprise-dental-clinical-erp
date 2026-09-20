<script setup lang="ts">
/**
 * Sparkline — tiny inline trend chart (SVG).
 *
 * Inert by default. Keep it small (≤ 60px tall) — sits next to KPI numbers
 * to give a temporal cue without stealing focus from the value.
 */
type Tone = 'primary' | 'success' | 'danger' | 'info' | 'warning' | 'neutral'

interface Props {
  points: number[]
  /** Visual height in px. Width fills container. */
  height?: number
  tone?: Tone
  /** Fill area below the line with a soft tint of the tone. */
  area?: boolean
  /** Accessible label override. Default builds one from min/max. */
  ariaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: 36,
  tone: 'primary',
  area: true,
  ariaLabel: undefined
})

const toneVar = computed(() => {
  const map: Record<Tone, string> = {
    primary: 'var(--color-primary)',
    success: 'var(--color-success-accent)',
    danger: 'var(--color-danger-accent)',
    info: 'var(--color-info-accent)',
    warning: 'var(--color-warning-accent)',
    neutral: 'var(--color-text-muted)'
  }
  return map[props.tone]
})

const W = 100
const H = computed(() => props.height)

const path = computed(() => {
  const pts = props.points
  if (pts.length < 2) return { line: '', area: '' }
  const min = Math.min(...pts)
  const max = Math.max(...pts)
  const span = max - min || 1
  const stepX = W / (pts.length - 1)
  const coords = pts.map((v, i) => {
    const x = i * stepX
    const y = H.value - ((v - min) / span) * (H.value - 4) - 2
    return [x, y] as const
  })
  const line = coords.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ')
  const areaPath = `${line} L${W},${H.value} L0,${H.value} Z`
  return { line, area: areaPath }
})

const label = computed(() => {
  if (props.ariaLabel) return props.ariaLabel
  if (!props.points.length) return 'sparkline empty'
  const last = props.points[props.points.length - 1]
  const first = props.points[0]
  const delta = last! - first!
  return `Trend ${props.points.length} points, ${delta >= 0 ? 'up' : 'down'} ${Math.abs(delta).toFixed(0)}`
})

const isEmpty = computed(() => props.points.length < 2)
</script>

<template>
  <div
    class="block w-full"
    :style="{ height: `${H}px` }"
  >
    <svg
      v-if="!isEmpty"
      :viewBox="`0 0 ${W} ${H}`"
      preserveAspectRatio="none"
      role="img"
      :aria-label="label"
      class="w-full h-full overflow-visible"
    >
      <path
        v-if="area"
        :d="path.area"
        :fill="toneVar"
        fill-opacity="0.12"
      />
      <path
        :d="path.line"
        :stroke="toneVar"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
      />
    </svg>
    <div
      v-else
      class="h-full w-full rounded bg-surface-muted"
      aria-hidden="true"
    />
  </div>
</template>

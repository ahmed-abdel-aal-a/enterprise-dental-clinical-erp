<script setup lang="ts">
/**
 * Onboarding mini-modal: set the weekly clinic hours without leaving the
 * dashboard. Same grid + composable as `ClinicHoursPage`, plus two preset
 * chips for the common patterns. Emits `saved` after a successful write.
 */
import type { WeekdayShifts } from '../../composables/useClinicHours'
import { errorDetail } from '~~/app/utils/error'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', v: boolean): void, (e: 'saved'): void }>()

const { t } = useI18n()
const toast = useToast()
const { fetchHours, updateHours } = useClinicHours()

const isOpen = computed({
  get: () => props.open,
  set: (v: boolean) => emit('update:open', v)
})

const days = ref<WeekdayShifts[]>([])
const isLoading = ref(false)
const isSaving = ref(false)

const PRESETS: Record<'split' | 'continuous', Array<{ start_time: string, end_time: string }>> = {
  split: [{ start_time: '09:00', end_time: '14:00' }, { start_time: '16:00', end_time: '20:00' }],
  continuous: [{ start_time: '09:00', end_time: '18:00' }]
}

function applyPreset(key: keyof typeof PRESETS) {
  days.value = Array.from({ length: 7 }, (_, weekday) => ({
    weekday,
    shifts: weekday < 5 ? PRESETS[key].map(s => ({ ...s })) : []
  }))
}

watch(() => props.open, async (open) => {
  if (!open) return
  isLoading.value = true
  try {
    days.value = (await fetchHours()).days
  } catch {
    applyPreset('split')
  } finally {
    isLoading.value = false
  }
}, { immediate: true }) // mounted lazily with open=true — load on first render too

async function save() {
  isSaving.value = true
  try {
    await updateHours({
      days: days.value.map(d => ({
        weekday: d.weekday,
        shifts: d.shifts.map(s => ({ start_time: s.start_time, end_time: s.end_time }))
      }))
    })
    toast.add({ title: t('schedules.clinicHours.saved'), color: 'success' })
    emit('saved')
    isOpen.value = false
  } catch (e) {
    toast.add({ title: t('schedules.clinicHours.savedError'), description: errorDetail(e), color: 'error' })
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :ui="{ content: 'max-w-2xl' }"
  >
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-clock"
              class="w-5 h-5 text-primary-accent"
            />
            <div>
              <h3 class="font-semibold text-default">
                {{ t('schedules.clinicHours.title') }}
              </h3>
              <p class="text-caption text-muted">
                {{ t('schedules.clinicHours.subtitle') }}
              </p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <UButton
              size="sm"
              variant="soft"
              color="neutral"
              icon="i-lucide-sun-medium"
              @click="applyPreset('split')"
            >
              {{ t('schedules.onboarding.presetSplit') }}
            </UButton>
            <UButton
              size="sm"
              variant="soft"
              color="neutral"
              icon="i-lucide-sun"
              @click="applyPreset('continuous')"
            >
              {{ t('schedules.onboarding.presetContinuous') }}
            </UButton>
          </div>

          <div class="max-h-[60vh] overflow-y-auto">
            <USkeleton
              v-if="isLoading"
              class="h-40 w-full"
            />
            <WeeklyShiftGrid
              v-else
              v-model="days"
            />
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <UButton
              variant="ghost"
              @click="isOpen = false"
            >
              {{ t('common.cancel') }}
            </UButton>
            <UButton
              :loading="isSaving"
              @click="save"
            >
              {{ t('schedules.clinicHours.save') }}
            </UButton>
          </div>
        </div>
      </UCard>
    </template>
  </UModal>
</template>

<script setup lang="ts">
/**
 * BranchSwitcher — Header component allowing the user to select the active clinic branch
 * or navigate to branch management settings.
 */
import type { Branch } from '~/types'

const { t } = useI18n()
const router = useRouter()
const {
  currentBranch,
  activeBranches,
  switchBranch,
  fetchBranches,
  isLoading
} = useBranch()

onMounted(async () => {
  if (activeBranches.value.length === 0) {
    await fetchBranches()
  }
})

const items = computed(() => {
  const branchItems = activeBranches.value.map((b: Branch) => ({
    label: b.name,
    icon: b.is_main ? 'i-lucide-building-2' : 'i-lucide-map-pin',
    color: b.id === currentBranch.value?.id ? ('primary' as const) : undefined,
    badge: b.is_main ? t('branch.main', 'الرئيسي') : undefined,
    class: b.id === currentBranch.value?.id ? 'font-semibold text-primary' : '',
    onSelect: () => switchBranch(b.id)
  }))

  const actions = [
    {
      label: t('branch.manage', 'إدارة الفروع'),
      icon: 'i-lucide-settings-2',
      onSelect: () => router.push('/settings/branches')
    }
  ]

  return [branchItems, actions]
})
</script>

<template>
  <div class="inline-flex items-center">
    <UDropdownMenu :items="items">
      <UButton
        variant="subtle"
        color="neutral"
        size="xs"
        icon="i-lucide-map-pin"
        trailing-icon="i-lucide-chevrons-up-down"
        class="max-w-[180px] sm:max-w-[220px] font-medium"
        :loading="isLoading"
      >
        <span class="truncate">
          {{ currentBranch?.name || t('branch.select', 'اختر الفرع') }}
        </span>
        <UBadge
          v-if="currentBranch?.is_main"
          color="primary"
          variant="subtle"
          size="xs"
          class="hidden sm:inline-flex text-[10px] px-1 py-0"
        >
          {{ t('branch.main', 'الرئيسي') }}
        </UBadge>
      </UButton>
    </UDropdownMenu>
  </div>
</template>

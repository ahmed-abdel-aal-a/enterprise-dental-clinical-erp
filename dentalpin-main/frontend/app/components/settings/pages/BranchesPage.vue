<script setup lang="ts">
/**
 * BranchesPage — Management page for clinic branches.
 * Allows listing, creating, editing, and deactivating branches with
 * protection against deactivating the main branch.
 */
import type { Branch } from '~/types'

const { t } = useI18n()
const { branches, isLoading, fetchBranches, deleteBranch } = useBranch()
const { isAdmin } = usePermissions()

const showForm = ref(false)
const editing = ref<Branch | null>(null)

const showDelete = ref(false)
const isDeleting = ref(false)
const toDelete = ref<Branch | null>(null)

onMounted(async () => {
  await fetchBranches()
})

function openCreate() {
  editing.value = null
  showForm.value = true
}

function openEdit(branch: Branch) {
  editing.value = branch
  showForm.value = true
}

function openDelete(branch: Branch) {
  toDelete.value = branch
  showDelete.value = true
}

async function handleDelete() {
  if (!toDelete.value) return
  isDeleting.value = true
  const success = await deleteBranch(toDelete.value.id)
  isDeleting.value = false
  if (success) {
    showDelete.value = false
    toDelete.value = null
    await fetchBranches()
  }
}
</script>

<template>
  <SectionCard
    icon="i-lucide-map-pin"
    :title="t('branch.title', 'فروع العيادة')"
  >
    <template
      v-if="isAdmin"
      #actions
    >
      <UButton
        icon="i-lucide-plus"
        size="xs"
        variant="ghost"
        @click="openCreate"
      >
        {{ t('branch.new', 'إضافة فرع جديد') }}
      </UButton>
    </template>

    <p class="text-caption text-subtle mb-4">
      {{ t('branch.description', 'إدارة فروع ومواقع العيادة، ومتابعة غرف الكشف والمواعيد والفواتير بشكل مستقل لكل فرع.') }}
    </p>

    <div
      v-if="isLoading"
      class="space-y-3"
    >
      <USkeleton class="h-14 w-full" />
      <USkeleton class="h-14 w-full" />
    </div>

    <div v-else>
      <div
        v-if="branches.length === 0"
        class="text-muted py-4 text-center"
      >
        {{ t('branch.noBranches', 'لا توجد فروع مسجلة') }}
      </div>

      <ul
        v-else
        class="divide-y divide-[var(--color-border-subtle)]"
      >
        <li
          v-for="branch in branches"
          :key="branch.id"
          class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-3.5"
        >
          <div class="flex items-start gap-3 min-w-0">
            <div class="p-2 rounded-lg bg-[var(--color-surface-subtle)] shrink-0 mt-0.5">
              <UIcon
                :name="branch.is_main ? 'i-lucide-building-2' : 'i-lucide-map-pin'"
                class="w-5 h-5"
                :class="branch.is_main ? 'text-primary' : 'text-subtle'"
              />
            </div>

            <div class="min-w-0 space-y-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-semibold text-default">{{ branch.name }}</span>
                <UBadge
                  v-if="branch.code"
                  variant="subtle"
                  color="neutral"
                  size="xs"
                >
                  {{ branch.code }}
                </UBadge>
                <UBadge
                  v-if="branch.is_main"
                  variant="solid"
                  color="primary"
                  size="xs"
                >
                  {{ t('branch.main', 'الفرع الرئيسي') }}
                </UBadge>
                <UBadge
                  v-if="!branch.is_active"
                  variant="outline"
                  color="error"
                  size="xs"
                >
                  {{ t('common.inactive', 'غير نشط') }}
                </UBadge>
              </div>

              <div class="text-xs text-subtle flex flex-wrap items-center gap-x-4 gap-y-1">
                <span
                  v-if="branch.phone"
                  class="flex items-center gap-1"
                >
                  <UIcon
                    name="i-lucide-phone"
                    class="w-3.5 h-3.5"
                  />
                  {{ branch.phone }}
                </span>
                <span
                  v-if="branch.email"
                  class="flex items-center gap-1"
                >
                  <UIcon
                    name="i-lucide-mail"
                    class="w-3.5 h-3.5"
                  />
                  {{ branch.email }}
                </span>
                <span
                  v-if="branch.address?.city || branch.address?.street || branch.address?.state"
                  class="flex items-center gap-1"
                >
                  <UIcon
                    name="i-lucide-navigation"
                    class="w-3.5 h-3.5"
                  />
                  {{ [branch.address.street, branch.address.city, branch.address.state].filter(Boolean).join(', ') }}
                </span>
              </div>
            </div>
          </div>

          <div
            v-if="isAdmin"
            class="flex items-center gap-1 shrink-0 self-end sm:self-center"
          >
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              variant="ghost"
              color="neutral"
              :aria-label="t('common.edit', 'تعديل')"
              @click="openEdit(branch)"
            />
            <UButton
              v-if="!branch.is_main"
              icon="i-lucide-trash-2"
              size="xs"
              variant="ghost"
              color="error"
              :aria-label="t('common.delete', 'حذف')"
              @click="openDelete(branch)"
            />
          </div>
        </li>
      </ul>
    </div>

    <!-- Create / edit modal -->
    <SettingsBranchesBranchFormModal
      v-model:open="showForm"
      :branch="editing"
      @saved="fetchBranches"
    />

    <!-- Delete modal -->
    <UModal v-model:open="showDelete">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-alert-triangle"
                class="w-5 h-5 text-danger-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('branch.deleteConfirmTitle', 'تأكيد حذف / تعطيل الفرع') }}
              </h3>
            </div>
          </template>

          <p class="text-muted dark:text-subtle">
            {{ t('branch.deleteConfirmText', 'هل أنت متأكد من رغبتك في تعطيل هذا الفرع؟') }}
            <strong class="text-default">
              {{ toDelete?.name }}
            </strong>
          </p>
          <p class="mt-2 text-caption text-subtle">
            {{ t('branch.deleteNote', 'لن يتم حذف السجلات والفواتير والمواعيد السابقة المرتبطة بهذا الفرع، ولكن لن يمكن حجز مواعيد جديدة عليه.') }}
          </p>

          <div class="flex justify-end gap-2 pt-6">
            <UButton
              variant="ghost"
              @click="showDelete = false"
            >
              {{ t('common.cancel', 'إلغاء') }}
            </UButton>
            <UButton
              color="error"
              :loading="isDeleting"
              @click="handleDelete"
            >
              {{ t('common.delete', 'تعطيل الفرع') }}
            </UButton>
          </div>
        </UCard>
      </template>
    </UModal>
  </SectionCard>
</template>

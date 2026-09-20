<script setup lang="ts">
/**
 * Create / edit a clinic branch.
 * Emits `saved` after successful creation or update.
 */
import type { Branch, BranchCreate, BranchUpdate } from '~/types'

const props = defineProps<{
  open: boolean
  branch?: Branch | null
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'saved'): void
}>()

const { t } = useI18n()
const { createBranch, updateBranch } = useBranch()

const isOpen = computed({
  get: () => props.open,
  set: (v: boolean) => emit('update:open', v)
})

const isEdit = computed(() => !!props.branch)
const isSaving = ref(false)

const form = ref({
  name: '',
  code: '',
  phone: '',
  email: '',
  street: '',
  city: '',
  state: '',
  postal_code: '',
  is_main: false,
  is_active: true
})

watch(() => props.open, (open) => {
  if (!open) return
  if (props.branch) {
    form.value = {
      name: props.branch.name,
      code: props.branch.code || '',
      phone: props.branch.phone || '',
      email: props.branch.email || '',
      street: props.branch.address?.street || '',
      city: props.branch.address?.city || '',
      state: props.branch.address?.state || '',
      postal_code: props.branch.address?.postal_code || '',
      is_main: props.branch.is_main,
      is_active: props.branch.is_active
    }
  } else {
    form.value = {
      name: '',
      code: '',
      phone: '',
      email: '',
      street: '',
      city: '',
      state: '',
      postal_code: '',
      is_main: false,
      is_active: true
    }
  }
})

async function submit() {
  if (!form.value.name.trim()) return

  isSaving.value = true
  const address = (form.value.street || form.value.city || form.value.state || form.value.postal_code) ? {
    street: form.value.street || undefined,
    city: form.value.city || undefined,
    state: form.value.state || undefined,
    postal_code: form.value.postal_code || undefined
  } : undefined

  let result = null
  if (props.branch) {
    const payload: BranchUpdate = {
      name: form.value.name.trim(),
      code: form.value.code.trim() || null,
      phone: form.value.phone.trim() || null,
      email: form.value.email.trim() || null,
      address: address || null,
      is_main: form.value.is_main,
      is_active: form.value.is_active
    }
    result = await updateBranch(props.branch.id, payload)
  } else {
    const payload: BranchCreate = {
      name: form.value.name.trim(),
      code: form.value.code.trim() || undefined,
      phone: form.value.phone.trim() || undefined,
      email: form.value.email.trim() || undefined,
      address,
      is_main: form.value.is_main
    }
    result = await createBranch(payload)
  }

  isSaving.value = false
  if (result) {
    emit('saved')
    isOpen.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen">
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              :name="isEdit ? 'i-lucide-pencil' : 'i-lucide-plus-circle'"
              class="w-5 h-5 text-primary"
            />
            <h3 class="font-semibold text-default">
              {{ isEdit ? t('branch.edit', 'تعديل الفرع') : t('branch.new', 'فرع جديد') }}
            </h3>
          </div>
        </template>

        <form
          class="space-y-4"
          @submit.prevent="submit"
        >
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField
              :label="t('branch.name', 'اسم الفرع')"
              required
              class="sm:col-span-2"
            >
              <UInput
                v-model="form.name"
                class="w-full"
                required
                autofocus
                :placeholder="t('branch.namePlaceholder', 'مثال: الفرع الرئيسي - المعادي')"
              />
            </UFormField>

            <UFormField :label="t('branch.code', 'رمز الفرع')">
              <UInput
                v-model="form.code"
                class="w-full"
                :placeholder="t('branch.codePlaceholder', 'مثال: BR-01')"
              />
            </UFormField>

            <UFormField :label="t('branch.phone', 'رقم الهاتف')">
              <UInput
                v-model="form.phone"
                class="w-full"
                type="tel"
                :placeholder="t('branch.phonePlaceholder', '+20 100 000 0000')"
              />
            </UFormField>

            <UFormField
              :label="t('branch.email', 'البريد الإلكتروني')"
              class="sm:col-span-2"
            >
              <UInput
                v-model="form.email"
                class="w-full"
                type="email"
                :placeholder="t('branch.emailPlaceholder', 'branch@example.com')"
              />
            </UFormField>

            <UFormField
              :label="t('branch.street', 'الشارع / العنوان')"
              class="sm:col-span-2"
            >
              <UInput
                v-model="form.street"
                class="w-full"
                :placeholder="t('branch.streetPlaceholder', 'شارع النصر، عمارة 12')"
              />
            </UFormField>

            <UFormField :label="t('branch.city', 'المدينة')">
              <UInput
                v-model="form.city"
                class="w-full"
                :placeholder="t('branch.cityPlaceholder', 'القاهرة')"
              />
            </UFormField>

            <UFormField :label="t('branch.state', 'المحافظة / المنطقة')">
              <UInput
                v-model="form.state"
                class="w-full"
                :placeholder="t('branch.statePlaceholder', 'القاهرة')"
              />
            </UFormField>
          </div>

          <!-- Branch Flags -->
          <div class="pt-2 border-t border-[var(--color-border-subtle)] space-y-3">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="form.is_main"
                type="checkbox"
                class="rounded border-[var(--color-border)] text-primary focus:ring-primary"
                :disabled="isEdit && branch?.is_main"
              >
              <span class="text-sm font-medium text-default">
                {{ t('branch.isMain', 'تعيين كفرع رئيسي للعيادة') }}
              </span>
            </label>
            <p
              v-if="isEdit && branch?.is_main"
              class="text-xs text-subtle"
            >
              {{ t('branch.mainCannotChangeDirectly', 'هذا هو الفرع الرئيسي الحالي.') }}
            </p>

            <div
              v-if="isEdit"
              class="pt-1"
            >
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.is_active"
                  type="checkbox"
                  class="rounded border-[var(--color-border)] text-primary focus:ring-primary"
                  :disabled="branch?.is_main"
                >
                <span class="text-sm font-medium text-default">
                  {{ t('branch.isActive', 'الفرع نشط ويستقبل مواعيد وفواتير') }}
                </span>
              </label>
              <p
                v-if="branch?.is_main"
                class="text-xs text-danger-accent"
              >
                {{ t('branch.cannotDeactivateMain', 'لا يمكن تعطيل الفرع الرئيسي للعيادة.') }}
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-4 border-t border-[var(--color-border-subtle)]">
            <UButton
              variant="ghost"
              @click="isOpen = false"
            >
              {{ t('common.cancel', 'إلغاء') }}
            </UButton>
            <UButton
              type="submit"
              :loading="isSaving"
            >
              {{ isEdit ? t('settings.saveChanges', 'حفظ التعديلات') : t('branch.create', 'إنشاء الفرع') }}
            </UButton>
          </div>
        </form>
      </UCard>
    </template>
  </UModal>
</template>

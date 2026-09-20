<script setup lang="ts">
import { PERMISSIONS } from '~~/app/config/permissions'
import { useExpenses, type Expense, type ExpenseCategory, type ExpenseMonthlyTotal } from '../../composables/useExpenses'

definePageMeta({ middleware: ['auth'] })

const { t } = useI18n()
const { can } = usePermissions()
const { format: formatCurrency } = useCurrency()
const expensesApi = useExpenses()

if (!can(PERMISSIONS.expenses.read)) {
  await navigateTo('/')
}

const canWrite = computed(() => can(PERMISSIONS.expenses.write))

const CATEGORIES: ExpenseCategory[] = [
  'rent', 'utilities', 'salaries', 'supplies', 'equipment', 'insurance', 'maintenance', 'other'
]
const categoryOptions = computed(() =>
  CATEGORIES.map(c => ({ value: c, label: t(`expenses.categories.${c}`) }))
)

// --- List state (server-side pagination) ----------------------------------
const items = ref<Expense[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const PAGE_SIZE = 20
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const now = new Date()
const filterCategory = ref<ExpenseCategory | undefined>(undefined)

async function load() {
  loading.value = true
  try {
    const res = await expensesApi.list({
      category: filterCategory.value,
      page: page.value,
      page_size: PAGE_SIZE
    })
    items.value = res.data
    total.value = res.total
    // A filter change can drop us past the last page.
    if (page.value > totalPages.value) {
      page.value = totalPages.value
      await load()
    }
  } finally {
    loading.value = false
  }
}

function onPage(p: number) {
  page.value = p
  load()
}

const monthlyTotals = ref<ExpenseMonthlyTotal[]>([])
async function loadMonthlyTotals() {
  const res = await expensesApi.monthlyTotals(now.getFullYear(), now.getMonth() + 1)
  monthlyTotals.value = res.data
}

onMounted(async () => {
  await Promise.all([load(), loadMonthlyTotals()])
})

watch(filterCategory, () => {
  page.value = 1
  load()
})

// --- Add expense modal ---
const showModal = ref(false)
const saving = ref(false)
const form = ref({
  category: 'other' as ExpenseCategory,
  amount: 0,
  expense_date: new Date().toISOString().slice(0, 10),
  description: ''
})

async function submit() {
  saving.value = true
  try {
    await expensesApi.create({
      category: form.value.category,
      amount: form.value.amount,
      expense_date: form.value.expense_date,
      description: form.value.description || undefined
    })
    showModal.value = false
    form.value = { category: 'other', amount: 0, expense_date: new Date().toISOString().slice(0, 10), description: '' }
    await Promise.all([load(), loadMonthlyTotals()])
  } finally {
    saving.value = false
  }
}

// --- Delete confirmation (same pattern as the catalog settings page) ------
const showDeleteConfirm = ref(false)
const itemToDelete = ref<Expense | null>(null)
const isDeleting = ref(false)

function confirmDelete(expense: Expense) {
  itemToDelete.value = expense
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!itemToDelete.value) return
  isDeleting.value = true
  try {
    await expensesApi.remove(itemToDelete.value.id)
    showDeleteConfirm.value = false
    await Promise.all([load(), loadMonthlyTotals()])
  } finally {
    isDeleting.value = false
  }
}

const columns = [
  { accessorKey: 'expense_date', header: t('expenses.date') },
  { accessorKey: 'category', header: t('expenses.category') },
  { accessorKey: 'amount', header: t('expenses.amount') },
  { accessorKey: 'description', header: t('expenses.description') },
  { accessorKey: 'actions', header: '' }
]
</script>

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-h2 text-default">
        {{ t('expenses.title') }}
      </h1>
      <UButton
        v-if="canWrite"
        icon="i-lucide-plus"
        @click="showModal = true"
      >
        {{ t('expenses.add') }}
      </UButton>
    </div>

    <div class="flex flex-wrap gap-2">
      <UBadge
        v-for="mt in monthlyTotals"
        :key="mt.category"
        variant="subtle"
        size="sm"
      >
        {{ t(`expenses.categories.${mt.category}`) }}: {{ formatCurrency(mt.total) }}
      </UBadge>
    </div>

    <USelect
      v-model="filterCategory"
      :items="categoryOptions"
      :placeholder="t('expenses.filterByCategory')"
      class="max-w-xs"
    />

    <UTable
      :data="items"
      :columns="columns"
      :loading="loading"
    >
      <template #amount-cell="{ row }">
        <span class="tnum">{{ formatCurrency(row.original.amount) }}</span>
      </template>
      <template #actions-cell="{ row }">
        <UButton
          v-if="canWrite"
          icon="i-lucide-trash-2"
          variant="ghost"
          color="error"
          size="xs"
          :aria-label="t('expenses.delete')"
          @click="confirmDelete(row.original)"
        />
      </template>
    </UTable>

    <PaginationBar
      :page="page"
      :total-pages="totalPages"
      :total="total"
      :page-size="PAGE_SIZE"
      @update:page="onPage"
    />

    <UModal v-model:open="showModal">
      <template #content>
        <div class="p-4 space-y-4">
          <h2 class="text-h3 text-default">
            {{ t('expenses.add') }}
          </h2>
          <USelect
            v-model="form.category"
            :items="categoryOptions"
          />
          <UInput
            v-model.number="form.amount"
            type="number"
            step="0.01"
            :placeholder="t('expenses.amount')"
          />
          <UInput
            v-model="form.expense_date"
            type="date"
          />
          <UInput
            v-model="form.description"
            :placeholder="t('expenses.description')"
          />
          <div class="flex justify-end gap-2">
            <UButton
              variant="ghost"
              @click="showModal = false"
            >
              {{ t('actions.cancel') }}
            </UButton>
            <UButton
              :loading="saving"
              @click="submit"
            >
              {{ t('actions.save') }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete confirmation -->
    <UModal v-model:open="showDeleteConfirm">
      <template #content>
        <div class="p-4 space-y-4">
          <h2 class="text-h3 text-default">
            {{ t('expenses.deleteTitle') }}
          </h2>
          <p class="text-ui text-subtle">
            {{ t('expenses.deleteMessage') }}
          </p>
          <div class="flex justify-end gap-2">
            <UButton
              variant="ghost"
              @click="showDeleteConfirm = false"
            >
              {{ t('actions.cancel') }}
            </UButton>
            <UButton
              color="error"
              :loading="isDeleting"
              @click="handleDelete"
            >
              {{ t('expenses.delete') }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

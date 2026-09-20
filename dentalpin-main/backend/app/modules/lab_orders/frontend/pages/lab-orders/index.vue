<script setup lang="ts">
import { PERMISSIONS } from '~~/app/config/permissions'
import { useLabOrders, type OrderStatus } from '../../composables/useLabOrders'

definePageMeta({ middleware: ['auth'] })

const { t } = useI18n()
const { can } = usePermissions()
const api = useLabOrders()
const loading = ref(false)
const orders = ref<Awaited<ReturnType<typeof api.list>>['data']>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 20
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))
const statuses: OrderStatus[] = ['sent', 'in_progress', 'ready', 'received', 'cancelled']

if (!can(PERMISSIONS.labOrders.read)) await navigateTo('/')

async function load() {
  loading.value = true
  try {
    const response = await api.list({ page: page.value, page_size: PAGE_SIZE })
    orders.value = response.data
    total.value = response.total
  } finally {
    loading.value = false
  }
}

function onPage(p: number) {
  page.value = p
  load()
}

async function updateStatus(id: string, status: OrderStatus) {
  await api.update(id, { status })
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-h2 text-default">
        {{ t('labOrders.title') }}
      </h1>
      <UButton
        v-if="can(PERMISSIONS.labOrders.write)"
        to="/lab-orders/new"
        icon="i-lucide-plus"
      >
        {{ t('labOrders.add') }}
      </UButton>
    </div>
    <div
      v-if="loading"
      class="text-caption text-subtle"
    >
      {{ t('labOrders.loading') }}
    </div>
    <UTable
      v-else
      :data="orders"
      :columns="[
        { accessorKey: 'patient_name', header: t('labOrders.patient') },
        { accessorKey: 'lab_contact_name', header: t('labOrders.lab') },
        { accessorKey: 'work_type', header: t('labOrders.workType') },
        { accessorKey: 'sent_date', header: t('labOrders.sentDate') },
        { accessorKey: 'expected_date', header: t('labOrders.expectedDate') },
        { accessorKey: 'status', header: t('labOrders.status') }
      ]"
    >
      <template #status-cell="{ row }">
        <USelect
          v-if="can(PERMISSIONS.labOrders.write)"
          :model-value="row.original.status"
          :items="statuses.map(value => ({ value, label: t(`labOrders.statuses.${value}`) }))"
          @update:model-value="value => updateStatus(row.original.id, value as OrderStatus)"
        />
        <UBadge
          v-else
          variant="subtle"
        >
          {{ t(`labOrders.statuses.${row.original.status}`) }}
        </UBadge>
      </template>
    </UTable>

    <PaginationBar
      :page="page"
      :total-pages="totalPages"
      :total="total"
      :page-size="PAGE_SIZE"
      @update:page="onPage"
    />
  </div>
</template>

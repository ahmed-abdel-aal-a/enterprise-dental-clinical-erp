<script setup lang="ts">
import type { ApiResponse, PaginatedResponse } from '~~/app/types'
import { PERMISSIONS } from '~~/app/config/permissions'
import { useActivityJournal, JOURNAL_EVENT_TYPES, type JournalEntry } from '../../composables/useActivityJournal'

definePageMeta({ middleware: ['auth'] })

const { t } = useI18n()
const { can } = usePermissions()
const api = useApi()
const journalApi = useActivityJournal()

if (!can(PERMISSIONS.activityJournal.read)) {
  await navigateTo('/')
}

// --- List state (server-side pagination) ----------------------------------
const items = ref<JournalEntry[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const PAGE_SIZE = 20
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const filterType = ref<string>('all')
const filterDateFrom = ref<string>('')
const filterDateTo = ref<string>('')

const eventTypeOptions = computed(() => [
  { value: 'all', label: t('journal.allEvents') },
  ...JOURNAL_EVENT_TYPES.map(v => ({ value: v, label: v }))
])

// --- Actor / patient name resolution --------------------------------------
// Ids in journal rows are loose references (no FKs); resolve them to
// names client-side and fall back to a short id when lookup fails
// (deleted rows, or a viewer without users.read / patients.read).
const userNames = ref<Record<string, string>>({})
const patientNames = ref<Record<string, string>>({})

async function loadUserNames() {
  try {
    const res = await api.get<PaginatedResponse<{ id: string, first_name: string, last_name: string }>>('/api/v1/auth/users')
    userNames.value = Object.fromEntries(
      res.data.map(u => [u.id, `${u.first_name} ${u.last_name}`.trim()])
    )
  } catch {
    // Not admin — actor cells fall back to short ids.
  }
}

async function resolvePatientNames(entries: JournalEntry[]) {
  const missing = [...new Set(
    entries.map(e => e.patient_id).filter((id): id is string => !!id && !(id in patientNames.value))
  )]
  await Promise.all(missing.map(async (id) => {
    try {
      const res = await api.get<ApiResponse<{ first_name: string, last_name: string }>>(`/api/v1/patients/${id}`)
      patientNames.value[id] = `${res.data.first_name} ${res.data.last_name}`.trim()
    } catch {
      patientNames.value[id] = id.slice(0, 8)
    }
  }))
}

async function load() {
  loading.value = true
  try {
    const res = await journalApi.list({
      event_type: filterType.value === 'all' ? undefined : filterType.value,
      date_from: filterDateFrom.value || undefined,
      date_to: filterDateTo.value || undefined,
      page: page.value,
      page_size: PAGE_SIZE
    })
    items.value = res.data
    total.value = res.total
    resolvePatientNames(res.data)
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

watch([filterType, filterDateFrom, filterDateTo], () => {
  page.value = 1
  load()
})

function fmtWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  })
}

const columns = computed(() => [
  { accessorKey: 'occurred_at', header: t('journal.when') },
  { accessorKey: 'event_type', header: t('journal.event') },
  { accessorKey: 'actor_id', header: t('journal.actor') },
  { accessorKey: 'patient_id', header: t('journal.patient') },
  { accessorKey: 'source_table', header: t('journal.source') },
  { id: 'actions', header: '' }
])

// --- Payload detail modal (read-only) --------------------------------------
const showDetail = ref(false)
const selected = ref<JournalEntry | null>(null)

function openDetail(entry: JournalEntry) {
  selected.value = entry
  showDetail.value = true
}

const prettyPayload = computed(() =>
  selected.value ? JSON.stringify(selected.value.payload, null, 2) : ''
)

onMounted(() => {
  loadUserNames()
  load()
})
</script>

<template>
  <div class="space-y-4 p-4">
    <div>
      <h1 class="text-h3 text-default">
        {{ t('journal.title') }}
      </h1>
      <p class="text-ui text-subtle">
        {{ t('journal.subtitle') }}
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <USelect
        v-model="filterType"
        :items="eventTypeOptions"
        :placeholder="t('journal.filterByType')"
        class="w-72 max-w-full"
      />
      <UInput
        v-model="filterDateFrom"
        type="date"
        :placeholder="t('journal.filterByDateFrom')"
      />
      <UInput
        v-model="filterDateTo"
        type="date"
        :placeholder="t('journal.filterByDateTo')"
      />
    </div>

    <UTable
      :data="items"
      :columns="columns"
      :loading="loading"
      :empty="t('journal.empty')"
    >
      <template #occurred_at-cell="{ row }">
        <span class="tnum">{{ fmtWhen(row.original.occurred_at) }}</span>
      </template>
      <template #event_type-cell="{ row }">
        <UBadge
          variant="subtle"
          size="sm"
        >
          {{ row.original.event_type }}
        </UBadge>
      </template>
      <template #actor_id-cell="{ row }">
        <span v-if="row.original.actor_id">
          {{ userNames[row.original.actor_id] ?? row.original.actor_id.slice(0, 8) }}
        </span>
        <span
          v-else
          class="text-subtle"
        >{{ t('journal.unattributed') }}</span>
      </template>
      <template #patient_id-cell="{ row }">
        <NuxtLink
          v-if="row.original.patient_id"
          :to="`/patients/${row.original.patient_id}`"
          class="text-primary hover:underline"
        >
          {{ patientNames[row.original.patient_id] ?? row.original.patient_id.slice(0, 8) }}
        </NuxtLink>
        <span
          v-else
          class="text-subtle"
        >{{ t('journal.unattributed') }}</span>
      </template>
      <template #actions-cell="{ row }">
        <UButton
          icon="i-lucide-eye"
          variant="ghost"
          size="sm"
          :aria-label="t('journal.viewPayload')"
          @click="openDetail(row.original)"
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

    <!-- Payload detail -->
    <UModal v-model:open="showDetail">
      <template #content>
        <div class="p-4 space-y-4 max-w-2xl">
          <h2 class="text-h3 text-default">
            {{ t('journal.detailTitle') }}
          </h2>
          <pre class="text-xs bg-elevated p-3 rounded overflow-auto max-h-96">{{ prettyPayload }}</pre>
          <div class="flex justify-end">
            <UButton
              variant="ghost"
              @click="showDetail = false"
            >
              {{ t('actions.close') }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

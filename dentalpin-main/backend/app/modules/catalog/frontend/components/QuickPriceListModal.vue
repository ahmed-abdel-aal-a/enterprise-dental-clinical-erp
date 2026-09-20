<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'updated'): void
}>()

const api = useApi()
const toast = useToast()

interface PriceItem {
  id: string
  internal_code: string
  names: Record<string, string>
  category_key?: string
  default_price: number
  is_default_for_type: boolean
  odontogram_treatment_type?: string
  // Local edit buffer
  edit_price?: number
}

const items = ref<PriceItem[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const selectedFilter = ref<'all' | 'odontogram' | 'diagnostics' | 'endo' | 'rest'>('odontogram')

watch(() => props.open, async (newVal) => {
  if (newVal) {
    await fetchPrices()
  }
}, { immediate: true })

async function fetchPrices() {
  isLoading.value = true
  try {
    const res = await api.get<any>('/api/v1/catalog/quick-prices')
    items.value = (res.data || []).map((item: any) => ({
      ...item,
      default_price: Number(item.default_price),
      edit_price: Number(item.default_price)
    }))
  } catch (err: any) {
    toast.add({ title: 'خطأ', description: 'تعذر جلب قائمة الأسعار', color: 'red' })
  } finally {
    isLoading.value = false
  }
}

const filteredItems = computed(() => {
  return items.value.filter(item => {
    // Filter type
    if (selectedFilter.value === 'odontogram' && !item.is_default_for_type) {
      return false
    }
    if (selectedFilter.value === 'diagnostics' && !item.internal_code.startsWith('DX-')) {
      return false
    }
    if (selectedFilter.value === 'endo' && !item.internal_code.startsWith('ENDO-')) {
      return false
    }
    if (selectedFilter.value === 'rest' && !item.internal_code.startsWith('REST-')) {
      return false
    }

    // Search query
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase()
      const arName = (item.names?.ar || '').toLowerCase()
      const enName = (item.names?.en || '').toLowerCase()
      const code = item.internal_code.toLowerCase()
      return arName.includes(q) || enName.includes(q) || code.includes(q)
    }

    return true
  })
})

const hasChanges = computed(() => {
  return items.value.some(item => Number(item.edit_price) !== Number(item.default_price))
})

async function savePrices() {
  const modified = items.value.filter(item => Number(item.edit_price) !== Number(item.default_price))
  if (!modified.length) {
    toast.add({ title: 'تنبيه', description: 'لم يتم تعديل أي أسعار', color: 'amber' })
    return
  }

  isSaving.value = true
  try {
    const payload = {
      items: modified.map(m => ({
        id: m.id,
        default_price: Number(m.edit_price)
      }))
    }
    await api.post('/api/v1/catalog/quick-prices', payload)
    toast.add({
      title: 'تم تحديث الأسعار بنجاح',
      description: `تم حفظ وتعديل أسعار ${modified.length} خدمة`,
      color: 'green'
    })
    // Update baseline
    modified.forEach(m => {
      m.default_price = Number(m.edit_price)
    })
    emit('updated')
    emit('update:open', false)
  } catch (err: any) {
    toast.add({ title: 'خطأ', description: err.message || 'فشل حفظ الأسعار', color: 'red' })
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <UModal :open="open" @update:open="$emit('update:open', $event)">
    <template #content>
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100 dark:divide-gray-800' }">
        <template #header>
        <div class="flex items-center justify-between" dir="rtl">
          <div class="flex items-center gap-2">
            <div class="p-2 bg-amber-100 dark:bg-amber-950 text-amber-600 rounded-lg">
              <UIcon name="i-lucide-tags" class="w-6 h-6" />
            </div>
            <div>
              <h3 class="text-base font-bold text-gray-900 dark:text-white">
                تسعيرة خدمات العيادة (ضبط الأسعار السريعة)
              </h3>
              <p class="text-xs text-gray-500">
                عدّل أسعار الكشوفات والحشوات والعلاجات مرة واحدة لتُحسب تلقائياً في الكاشير ومخطط الأسنان.
              </p>
            </div>
          </div>
          <UButton color="gray" variant="ghost" icon="i-lucide-x" @click="$emit('update:open', false)" />
        </div>
      </template>

      <div class="space-y-4 py-2" dir="rtl">
        <!-- Filter Tabs & Search -->
        <div class="flex flex-col sm:flex-row gap-2 justify-between items-stretch sm:items-center">
          <div class="flex flex-wrap gap-1">
            <UButton size="xs" :color="selectedFilter === 'odontogram' ? 'primary' : 'gray'"
                     :variant="selectedFilter === 'odontogram' ? 'solid' : 'soft'"
                     @click="selectedFilter = 'odontogram'">
              ⭐ خدمات مخطط الأسنان (16)
            </UButton>
            <UButton size="xs" :color="selectedFilter === 'diagnostics' ? 'primary' : 'gray'"
                     :variant="selectedFilter === 'diagnostics' ? 'solid' : 'soft'"
                     @click="selectedFilter = 'diagnostics'">
              كشوفات وأشعة
            </UButton>
            <UButton size="xs" :color="selectedFilter === 'rest' ? 'primary' : 'gray'"
                     :variant="selectedFilter === 'rest' ? 'solid' : 'soft'"
                     @click="selectedFilter = 'rest'">
              حشوات وتركيبات
            </UButton>
            <UButton size="xs" :color="selectedFilter === 'endo' ? 'primary' : 'gray'"
                     :variant="selectedFilter === 'endo' ? 'solid' : 'soft'"
                     @click="selectedFilter = 'endo'">
              علاج جذور وعصب
            </UButton>
            <UButton size="xs" :color="selectedFilter === 'all' ? 'primary' : 'gray'"
                     :variant="selectedFilter === 'all' ? 'solid' : 'soft'"
                     @click="selectedFilter = 'all'">
              الكل (129)
            </UButton>
          </div>

          <div class="w-full sm:w-48">
            <UInput v-model="searchQuery" placeholder="بحث باسم الخدمة..." icon="i-lucide-search" size="xs" />
          </div>
        </div>

        <!-- Price Table -->
        <div v-if="isLoading" class="py-12 text-center text-gray-500">
          <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin mx-auto mb-2 text-primary-500" />
          <p class="text-sm">جاري جلب تسعيرة العيادة...</p>
        </div>

        <div v-else class="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden max-h-96 overflow-y-auto">
          <table class="w-full text-xs text-right">
            <thead class="bg-gray-50 dark:bg-gray-800/60 sticky top-0 text-gray-500 font-medium border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th class="py-2.5 px-3">الخدمة الطبية</th>
                <th class="py-2.5 px-3">الكود</th>
                <th class="py-2.5 px-3 w-32">السعر بالجنيه (ج.م)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800 font-sans">
              <tr v-for="item in filteredItems" :key="item.id" class="hover:bg-gray-50/70 dark:hover:bg-gray-800/40">
                <td class="py-2 px-3">
                  <div class="flex items-center gap-1.5">
                    <span v-if="item.is_default_for_type" class="text-amber-500 font-bold" title="الخيار الافتراضي لمخطط الأسنان">⭐</span>
                    <span class="font-bold text-gray-800 dark:text-gray-200">
                      {{ item.names?.ar || item.names?.en }}
                    </span>
                  </div>
                </td>
                <td class="py-2 px-3 font-mono text-[11px] text-gray-500">
                  {{ item.internal_code }}
                </td>
                <td class="py-2 px-3">
                  <div class="flex items-center gap-1">
                    <input v-model.number="item.edit_price" type="number" min="0" step="50"
                           class="w-24 px-2 py-1 text-sm font-mono font-bold text-left border rounded bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 focus:ring-1 focus:ring-primary-500 focus:outline-none" />
                    <span class="text-gray-500 text-[11px]">ج</span>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredItems.length">
                <td colspan="3" class="py-8 text-center text-gray-400">
                  لا توجد خدمات مطابقة لبحثك
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between" dir="rtl">
          <span class="text-xs text-gray-500">
            {{ hasChanges ? 'هناك تعديلات لم تُحفظ بعد' : 'جميع الأسعار متزامنة مع العيادة' }}
          </span>
          <div class="flex gap-2">
            <UButton color="gray" variant="soft" @click="$emit('update:open', false)">
              إغلاق
            </UButton>
            <UButton color="amber" icon="i-lucide-save" :loading="isSaving" :disabled="!hasChanges" @click="savePrices">
              حفظ التسعيرة الجديدة
            </UButton>
          </div>
        </div>
      </template>
    </UCard>
  </template>
</UModal>
</template>

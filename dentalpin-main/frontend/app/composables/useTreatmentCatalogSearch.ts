/**
 * Shared state for treatment-catalog selectors (single + multi).
 * Loads popular items on demand and runs a debounce-free search over the
 * catalog API. Owns the loading flags so both selectors can share UX.
 */
import type { TreatmentCatalogItem, ApiResponse } from '~/types'

export function useTreatmentCatalogSearch() {
  const api = useApi()
  const { searchItems, getItemName, formatPrice } = useCatalog()
  const { locale } = useI18n()

  const popularItems = ref<TreatmentCatalogItem[]>([])
  const searchResults = ref<TreatmentCatalogItem[]>([])
  const isSearching = ref(false)
  const isLoadingPopular = ref(false)

  async function loadPopularItems() {
    isLoadingPopular.value = true
    try {
      const response = await api.get<ApiResponse<TreatmentCatalogItem[]>>(
        '/api/v1/catalog/items/popular?limit=8'
      )
      popularItems.value = response.data
    } catch {
      popularItems.value = []
    } finally {
      isLoadingPopular.value = false
    }
  }

  async function search(query: string) {
    if (!query || query.length < 2) {
      searchResults.value = []
      return
    }
    isSearching.value = true
    try {
      const results = await searchItems(query, 12)
      searchResults.value = results as unknown as TreatmentCatalogItem[]
    } catch {
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  function getCategoryName(item: TreatmentCatalogItem): string {
    if (item.category && item.category.names) {
      return item.category.names[locale.value] || item.category.names.es || ''
    }
    return ''
  }

  return {
    popularItems,
    searchResults,
    isSearching,
    isLoadingPopular,
    loadPopularItems,
    search,
    getItemName,
    formatPrice,
    getCategoryName
  }
}

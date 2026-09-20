<template>
  <div
    v-if="isOfflineMode || pendingCount > 0"
    class="w-full bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between transition-all"
    dir="rtl"
  >
    <div class="flex items-center gap-2">
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
      </span>
      <span class="font-medium">
        {{ isOfflineMode ? 'وضع الموبايل الليلي 24/7 (تصفح فوري من ذاكرة الهاتف)' : 'متصل بالعيادة' }}
      </span>
      <span
        v-if="pendingCount > 0"
        class="bg-amber-500/20 text-amber-900 dark:text-amber-100 font-semibold px-2 py-0.5 rounded-full"
      >
        {{ pendingCount }} عملية بانتظار المزامنة
      </span>
    </div>

    <div class="flex items-center gap-2">
      <button
        type="button"
        :disabled="syncing"
        @click="triggerSync"
        class="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded shadow-xs text-xs flex items-center gap-1 disabled:opacity-50 transition"
      >
        <span v-if="syncing" class="inline-block animate-spin">⟳</span>
        <span>{{ syncing ? 'جاري المزامنة...' : 'مزامنة الآن' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const outbox = useOutbox()
const { isOfflineMode, pendingCount, syncing } = outbox

onMounted(() => {
  outbox.refreshPendingCount()
  if (import.meta.client) {
    window.addEventListener('online', () => {
      outbox.syncOutbox()
    })
  }
})

async function triggerSync() {
  await outbox.syncOutbox()
}
</script>

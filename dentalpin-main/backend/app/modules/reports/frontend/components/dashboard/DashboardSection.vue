<script setup lang="ts">
interface Props {
  title?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  title: undefined,
  description: undefined
})
</script>

<template>
  <section class="space-y-3">
    <header
      v-if="title"
      class="flex items-baseline justify-between gap-3"
    >
      <div class="min-w-0">
        <h2 class="text-h2 text-default truncate">
          {{ title }}
        </h2>
        <p
          v-if="description"
          class="text-caption text-muted truncate"
        >
          {{ description }}
        </p>
      </div>
      <slot name="trailing" />
    </header>
    <slot />
  </section>
</template>

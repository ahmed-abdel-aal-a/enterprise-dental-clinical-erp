<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { t } = useI18n()
</script>

<template>
  <SettingsLayout
    active-id="workspace"
    :title="t('branch.title', 'فروع العيادة')"
    :subtitle="t('branch.description', 'إدارة فروع ومواقع العيادة، وغرف الكشف وتوافر الأطباء والفواتير.')"
    back-to="/settings/workspace"
    :back-label="t('settings.categories.workspace', 'مساحة العمل')"
  >
    <SettingsPagesBranchesPage />
  </SettingsLayout>
</template>

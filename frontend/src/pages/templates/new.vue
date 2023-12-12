<template>
  <split-menu v-model="localSettings.templateInputMenuSize">
    <template #menu>
      <template-field-selector />
    </template>

    <template #default>
      <template-editor v-model="template" :toolbar-attrs="toolbarAttrs" />
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { v4 as uuidv4 } from 'uuid';

useHeadExtended({
  title: 'Templates',
  breadcrumbs: () => templateListBreadcrumbs().concat([{ title: 'New', to: '/templates/new/' }]),
});

const apiSettings = useApiSettings();
const localSettings = useLocalSettings();
const templateStore = useTemplateStore();

const template = ref<FindingTemplate>({
  id: uuidv4(),
  tags: [],
  translations: [{
    id: uuidv4(),
    is_main: true,
    language: apiSettings.settings!.languages[0]?.code || 'en-US',
    status: ReviewStatus.IN_PROGRESS,
    data: {
      title: 'TODO: New Template Title',
    },
  }],
} as any as FindingTemplate)

async function performCreate() {
  const obj = await templateStore.create(template.value);
  await navigateTo(`/templates/${obj.id}/`);
}
const toolbarAttrs = computed(() => ({
  save: performCreate,
}));
</script>

<template>
  <full-height-page>
    <iframe :src="pluginMenuEntry.url" class="plugin-content" />
  </full-height-page>
</template>

<script setup lang="ts">
import { createError } from '#app';

const route = useRoute();
const apiSettings = useApiSettings();

const pluginMenuEntry = await useAsyncDataE(async () => {
  const pluginMenuEntry = apiSettings.pluginMenuEntries(PluginMenuId.PROJECT)
    .find(m => m.plugin.id === route.params.pluginId && m.id === route.params.menuEntryId);
  if (!pluginMenuEntry) {
    throw createError({ statusCode: 404 });
  }
  return pluginMenuEntry;
});

useHeadExtended({
  breadcrumbs: () => [
    { title: 'Plugins' },
    { title: pluginMenuEntry.value.title, to: route.fullPath },
  ]
});
</script>

<style lang="scss" scoped>
.plugin-content {
  display: block;
  height: 100%;
  width: 100%;
  border: 0;
}
</style>

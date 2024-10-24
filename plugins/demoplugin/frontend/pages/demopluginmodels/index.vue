<template>
  <list-view :url="`/api/plugins/${appConfig.pluginId}/api/demopluginmodels/`">
    <template #title>Demo Plugin Models</template>
    <template #actions>
      <btn-create @click="performCreate" />
    </template>
    <template #item="{ item }: { item: DemoPluginModel }">
      <v-list-item
        :title="item.name"
        :href="`/plugins/${appConfig.pluginId}/demopluginmodels/${item.id}/`"
        target="_top"
      />
    </template>
  </list-view>
</template>

<script setup lang="ts">
const appConfig = useAppConfig();

async function performCreate() {
  try {
    const obj = await $fetch<DemoPluginModel>(`/api/plugins/${appConfig.pluginId}/api/demopluginmodels/`, {
      method: 'POST',
      body: {
        name: 'New Demo Plugin Model',
      },
    });

    // When navigating, use the full path and specify target="_top" to open in the main window
    await navigateTo(`/plugins/${appConfig.pluginId}/demopluginmodels/${obj.id}/`, { open: { target: '_top' } });
  } catch (error: any) {
    requestErrorToast({ error });
  }
}
</script>
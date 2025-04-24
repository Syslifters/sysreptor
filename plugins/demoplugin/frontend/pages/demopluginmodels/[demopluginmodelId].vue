<template>
  <v-container fluid class="pt-0">
    <edit-toolbar v-bind="toolbarAttrs" ref="toolbarRef">
      <template #title>Demo Plugin Model Details</template>
    </edit-toolbar>

    <s-text-field
      v-model="obj.name"
      label="Name"
      spellcheck="false"
      class="mt-4"
    />
  </v-container>
</template>

<script setup lang="ts">
import type { DemoPluginModel } from '#imports';

const appConfig = useAppConfig();

const route = useRoute();

const obj = await useAsyncDataE(async () => {
  return await $fetch<DemoPluginModel>(`/api/plugins/${appConfig.pluginId}/api/demopluginmodels/${route.params.demopluginmodelId}`);
}, { deep: true });

const toolbarRef = useTemplateRef('toolbarRef');
const { toolbarAttrs, readonly } = useLockEdit<DemoPluginModel>({
  data: obj,
  toolbarRef,
  performSave: async () => {
    obj.value = await $fetch<DemoPluginModel>(`/api/plugins/${appConfig.pluginId}/api/demopluginmodels/${route.params.demopluginmodelId}/`, {
      method: 'PATCH',
      body: obj.value,
    });
  },
  performDelete: async () => {
    await $fetch(`/api/plugins/${appConfig.pluginId}/api/demopluginmodels/${route.params.demopluginmodelId}/`, {
      method: 'DELETE',
    });
    await navigateTo(`/plugins/${appConfig.pluginId}/demopluginmodels/`, { open: { target: '_top' } });
  },
  deleteConfirmInput: computed(() => obj.value.name),
});

</script>
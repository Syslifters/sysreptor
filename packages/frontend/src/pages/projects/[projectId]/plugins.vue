<template>
  <nuxt-page />
</template>

<script setup lang="ts">
definePageMeta({
  name: 'plugins-project',
});

const route = useRoute();
const projectStore = useProjectStore();

const project = await useAsyncDataE(async () => projectStore.getById(route.params.projectId as string));


useHeadExtended({
  breadcrumbs: () => projectDetailBreadcrumbs(project.value).concat(pluginBreadcrumbs(PluginRouteScope.PROJECT)),
});
</script>

<template>
  <nuxt-page />
</template>

<script setup lang="ts">
definePageMeta({
  name: 'plugins-main',
});
useAppBar({ breadcrumbs: () => pluginBreadcrumbs(PluginRouteScope.MAIN) });
</script>

<template>
  <nuxt-page />
</template>

<script setup lang="ts">
definePageMeta({
  name: 'plugins-main',
});
useHeadExtended({
  breadcrumbs: () => pluginBreadcrumbs(PluginRouteScope.MAIN),
});
</script>

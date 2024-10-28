<template>
  <v-container fluid class="pt-0">
    <h1>Sub-page of project {{ project.name }}</h1>
  </v-container>
</template>

<script setup lang="ts">
import type { PentestProject } from '#imports';

const route = useRoute();

const project = await useAsyncDataE(async () => {
  return await $fetch<PentestProject>(`/api/v1/pentestprojects/${route.params.projectId}/`);
})
</script>

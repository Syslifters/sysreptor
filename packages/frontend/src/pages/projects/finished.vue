<template>
  <list-view 
    url="/api/v1/pentestprojects/?readonly=true"
    v-model:ordering="localSettings.projectListOrdering"
    :ordering-options="[
      {id: 'created', title: 'Created', value: '-created'},
      {id: 'updated', title: 'Updated', value: '-updated'},
      {id: 'name', title: 'Name', value: 'name'},
    ]"
  >
    <template #title>Projects</template>
    <template #tabs>
      <v-tab :to="{path: '/projects/', query: route.query}" exact prepend-icon="mdi-file-document" text="Active" />
      <v-tab :to="{path: '/projects/finished/', query: route.query}" prepend-icon="mdi-flag-checkered" text="Finished" />
      <v-tab :to="{path: '/projects/archived/', query: route.query}" :disabled="!apiSettings.settings!.features.archiving" prepend-icon="mdi-folder-lock-outline">
        <pro-info>Archived</pro-info>
      </v-tab>
    </template>
    <template #item="{item}: {item: PentestProject}">
      <project-list-item :item="item" />
    </template>
  </list-view>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Projects',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => projectListBreadcrumbs(),
});

const route = useRoute();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
</script>

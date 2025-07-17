<template>
  <list-view 
    url="/api/v1/pentestprojects/?readonly=true"
    v-model:ordering="localSettings.projectListOrdering"
    :ordering-options="[
      {id: 'created', title: 'Created', value: '-created'},
      {id: 'updated', title: 'Updated', value: '-updated'},
      {id: 'name', title: 'Name', value: 'name'},
    ]"
    :filter-properties="filterProperties"
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

const filterProperties: FilterProperties[] = [
  { id: 'timerange', name: 'Time Created', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
  { id: 'language', name: 'Language', icon: 'mdi-translate', type: 'select', options: apiSettings.settings!.languages.map(l => l.code), allow_exclude: true, default: '', multiple: false },
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'text', options: [], allow_exclude: true, allow_regex: false, default: '', multiple: true },
];
</script>

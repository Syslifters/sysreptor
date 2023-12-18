<template>
  <file-drop-area @drop="importBtn.performImport($event)" class="h-100">
    <list-view url="/api/v1/pentestprojects/?readonly=false">
      <template #title>Projects</template>
      <template #actions>
        <btn-create to="/projects/new/" :disabled="!auth.permissions.value.create_projects" />
        <btn-import ref="importBtn" :import="performImport" :disabled="!auth.permissions.value.import_projects" />
      </template>
      <template #tabs>
        <v-tab :to="{path: '/projects/', query: route.query}" exact prepend-icon="mdi-file-document" text="Active" />
        <v-tab :to="{path: '/projects/finished/', query: route.query}" prepend-icon="mdi-flag-checkered" text="Finished" />
        <v-tab :to="{path: '/projects/archived/', query: route.query}" :disabled="!apiSettings.settings!.features.archiving" prepend-icon="mdi-folder-lock-outline">
          <pro-info>Archived</pro-info>
        </v-tab>
      </template>
      <template #item="{item}">
        <project-list-item :item="item" />
      </template>
    </list-view>
  </file-drop-area>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Projects',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => projectListBreadcrumbs(),
});

const auth = useAuth();
const route = useRoute();
const apiSettings = useApiSettings();

const importBtn = ref();
async function performImport(file: File) {
  const projects = await uploadFileHelper<PentestProject[]>('/api/v1/pentestprojects/import/', file);
  await navigateTo(`/projects/${projects[0].id}/`);
}
</script>

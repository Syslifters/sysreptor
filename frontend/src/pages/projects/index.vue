<template>
  <file-drop-area @drop="importBtn.performImport($event)" class="h-100">
    <full-height-page>
      <template #header>
        <s-sub-menu>
          <v-tab :to="`/projects/`" exact text="Active Projects" />
          <v-tab :to="`/projects/finished/`" text="Finished Projects" />
          <v-tab v-if="apiSettings.settings!.features.archiving" to="/projects/archived/" text="Archived Projects" />
        </s-sub-menu>
      </template>

      <list-view url="/api/v1/pentestprojects/?readonly=false">
        <template #title>Projects</template>
        <template #actions>
          <s-btn
            to="/projects/new/"
            color="primary"
            class="ml-1 mr-1"
            prepend-icon="mdi-plus"
            text="Create"
          />
          <btn-import ref="importBtn" :import="performImport" class="ml-1 mr-1" />
        </template>
        <template #item="{item}">
          <project-list-item :item="item" />
        </template>
      </list-view>
    </full-height-page>
  </file-drop-area>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Projects'
});

const apiSettings = useApiSettings();

const importBtn = ref();
async function performImport(file: File) {
  const projects = await uploadFileHelper<PentestProject[]>('/api/v1/pentestprojects/import/', file);
  await navigateTo(`/projects/${projects[0].id}/`);
}
</script>

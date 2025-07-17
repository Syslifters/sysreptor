<template>
  <file-drop-area @drop="importBtn?.performImport($event)" class="h-100">
    <list-view
      url="/api/v1/pentestprojects/?readonly=false&search=&ordering=-created" 
      v-model:ordering="localSettings.projectListOrdering"
      :ordering-options="[
        {id: 'created', title: 'Created', value: '-created'},
        {id: 'updated', title: 'Updated', value: '-updated'},
        {id: 'name', title: 'Name', value: 'name'},
      ]"
      :filter-properties="filterProperties"
      ref="listViewRef"
    >
      <template #title>Projects</template>
      <template #actions>
        <permission-info :value="auth.permissions.value.create_projects">
          <btn-create to="/projects/new/" :disabled="!auth.permissions.value.create_projects" />
        </permission-info>
        <permission-info :value="auth.permissions.value.import_projects">
          <btn-import ref="importBtn" :import="performImport" :disabled="!auth.permissions.value.import_projects" />
        </permission-info>
      </template>
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
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();

const importBtn = useTemplateRef('importBtn');
async function performImport(file: File) {
  const projects = await uploadFileHelper<PentestProject[]>('/api/v1/pentestprojects/import/', file);
  await navigateTo(`/projects/${projects[0]!.id}/`);
}

const listViewRef = ref();
const pentestMembers = ref<string[]>([]);

watchEffect(() => {
  if (!listViewRef.value?.items?.data.value || !Array.isArray(listViewRef.value.items.data.value)) {
    pentestMembers.value = [];
    return;
  }
  
  const allUsernames = new Set<string>(pentestMembers.value);
  listViewRef.value.items.data.value.forEach((project: PentestProject) => {
    if (project.members && Array.isArray(project.members)) {
      project.members.forEach(member => {
        allUsernames.add(member.username);
      });
    }
  });
  pentestMembers.value = Array.from(allUsernames).sort();
});

const filterProperties = computed((): FilterProperties[] => [
  { id: 'member', name: 'Member', icon: 'mdi-account', type: 'combobox', options: pentestMembers.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'text', options: [], allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'timerange', name: 'Time Created', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
  { id: 'language', name: 'Language', icon: 'mdi-translate', type: 'select', options: apiSettings.settings!.languages.map(l => l.code), allow_exclude: true, default: '', multiple: true },
]);
</script>

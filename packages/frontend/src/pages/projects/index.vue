<template>
  <file-drop-area @drop="importBtn?.performImport($event)" class="h-100">
    <list-view
      url="/api/v1/pentestprojects/?readonly=false" 
      v-model:ordering="localSettings.projectListOrdering"
      :ordering-options="[
        {id: 'created', title: 'Created', value: '-created'},
        {id: 'updated', title: 'Updated', value: '-updated'},
        {id: 'name', title: 'Name', value: 'name'},
      ]"
      v-model:pinned-filters="localSettings.projectListPinnedFilters"
      :filter-properties="filterProperties"
      :selectable="true"
      ref="listViewRef"
    >
      <template #title>Projects</template>
      <template #actions="{ selectedItems }">
        <permission-info :value="auth.permissions.value.create_projects">
          <btn-create to="/projects/new/" :disabled="!auth.permissions.value.create_projects" />
        </permission-info>
        <permission-info :value="auth.permissions.value.import_projects">
          <btn-import ref="importBtn" :import="performImport" :disabled="!auth.permissions.value.import_projects" />
        </permission-info>
        <template v-if="selectedItems.length > 0">
          <v-divider vertical />
          <permission-info :value="auth.permissions.value.delete_projects">
            <btn-delete
              :delete="() => performDeleteSelected(selectedItems as PentestProject[])"
              :disabled="selectedItems.length === 0"
              confirm-input="delete"
              color="error"
              tooltip-text="Delete selected"
              icon="mdi-delete"
            >
              <template #dialog-text>
                <p class="mt-0">
                  Do you really want to delete {{ selectedItems.length }} projects?
                </p>
                <ul class="mt-0">
                  <li v-for="p in selectedItems" :key="p.id">
                    {{ (p as PentestProject).name }}
                  </li>  
                </ul>
              </template>
            </btn-delete>
          </permission-info>
        </template>
      </template>
      <template #tabs>
        <v-tab :to="{path: '/projects/', query: route.query}" exact prepend-icon="mdi-file-document" text="Active" />
        <v-tab :to="{path: '/projects/finished/', query: route.query}" prepend-icon="mdi-flag-checkered" text="Finished" />
        <v-tab :to="{path: '/projects/archived/', query: route.query}" :disabled="!apiSettings.settings!.features.archiving" prepend-icon="mdi-folder-lock-outline">
          <pro-info>Archived</pro-info>
        </v-tab>
      </template>
      <template #item="{item}: {item: PentestProject}">
        <project-list-item :item="item" @filter="listViewRef?.addFilter($event)" />
      </template>
    </list-view>
  </file-drop-area>
</template>

<script setup lang="ts">
import { useProjectTags } from '@base/composables/tags';
import { sortBy, uniq } from 'lodash-es';

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
const projectStore = useProjectStore();

const importBtn = useTemplateRef('importBtn');
async function performImport(file: File) {
  const projects = await uploadFileHelper<PentestProject[]>('/api/v1/pentestprojects/import/', file);
  await navigateTo(`/projects/${projects[0]!.id}/`);
}

const listViewRef = useTemplateRef('listViewRef');
const suggestedMembers = ref<string[]>([]);
watch(() => listViewRef.value?.items?.data.value as PentestProject[]|undefined, (items) => {
  if (!items) { return; }
  suggestedMembers.value = sortBy(uniq(items.flatMap(p => p.members.map(member => member.username)).concat(suggestedMembers.value)));
}, { immediate: true, deep: 1 });
const suggestedTags = useProjectTags();
const filterProperties = computed((): FilterProperties[] => [
  { id: 'member', name: 'Member', icon: 'mdi-account', type: 'combobox', options: suggestedMembers.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'combobox', options: suggestedTags.getTags, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'timerange', name: 'Time Created', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
  { id: 'language', name: 'Language', icon: 'mdi-translate', type: 'select', options: apiSettings.settings!.languages.map(l => l.code), allow_exclude: true, default: '', multiple: true },
]);

async function performDeleteSelected(projects: PentestProject[]) {
  await bulkAction(projects, projectStore.deleteProject, p => `Failed to delete "${p.name}"`);
  await listViewRef.value?.refresh();
}

</script>

<template>
  <list-view 
    ref="listViewRef"
    url="/api/v1/pentestprojects/?readonly=true"
    v-model:ordering="localSettings.projectListOrdering"
    :ordering-options="[
      {id: 'created', title: 'Created', value: '-created'},
      {id: 'updated', title: 'Updated', value: '-updated'},
      {id: 'name', title: 'Name', value: 'name'},
    ]"
    v-model:pinned-filters="localSettings.projectListPinnedFilters"
    :filter-properties="filterProperties"
    :selectable="true"
  >
    <template #title>Projects</template>
    <template #navigation>
        <project-navigation-dropdown value="finished" />
      </template>
    <template #actions="{ selectedItems }: { selectedItems: PentestProject[] }">
      <template v-if="selectedItems.length > 0">
        <v-divider vertical />
        <s-btn-icon 
          icon="mdi-download"
          color="secondary"
          variant="flat"
          density="comfortable"
        >
          <v-icon icon="mdi-download" />
          <s-tooltip activator="parent" location="bottom" text="Export selected" />
          <v-menu activator="parent" location="bottom">
            <v-list>
              <btn-export
                export-url="/api/v1/pentestprojects/export/"
                :options="{ids: selectedItems.map(p => p.id), export_all: false}"
                name="projects"
                extension=".tar.gz"
              />
              <btn-export
                export-url="/api/v1/pentestprojects/export/"
                :options="{ids: selectedItems.map(p => p.id), export_all: true}"
                name="projects"
                extension=".tar.gz"
                button-text="Export (with notes)"
              />
            </v-list>
          </v-menu>
        </s-btn-icon>
        <permission-info :value="auth.permissions.value.update_project_settings">
          <btn-readonly
            :value="true"
            :set-readonly="() => setReadonlySelected(selectedItems)"
            :disabled="!auth.permissions.value.update_project_settings"
            :show-toast="false"
            button-variant="icon"
            variant="flat"
            density="comfortable"
          >
            <template #dialog-text>
              <p class="mt-0">
                Mark {{ selectedItems.length }} projects as active and allow editing?
              </p>
              <ul class="mt-0">
                <li v-for="p in selectedItems" :key="p.id">
                  {{ p.name }}
                </li>  
              </ul>
            </template>
          </btn-readonly>
        </permission-info>
        <permission-info :value="auth.permissions.value.delete_projects">
          <btn-delete
            :delete="() => performDeleteSelected(selectedItems)"
            :disabled="!auth.permissions.value.delete_projects"
            :confirm-input="`delete ${selectedItems.length} projects`"
            tooltip-text="Delete selected"
            icon="mdi-delete"
            density="comfortable"
          >
            <template #dialog-text>
              <p class="mt-0">
                Do you really want to delete {{ selectedItems.length }} projects?
              </p>
              <ul class="mt-0">
                <li v-for="p in selectedItems" :key="p.id">
                  {{ p.name }}
                </li>
              </ul>
            </template>
          </btn-delete>
        </permission-info>
      </template>
    </template>
    <template #item="{item}: {item: PentestProject}">
      <project-list-item :item="item" @filter="listViewRef?.addFilter($event)" />
    </template>
  </list-view>
</template>

<script setup lang="ts">
import { sortBy, uniq } from 'lodash-es';

definePageMeta({
  title: 'Projects',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => projectListBreadcrumbs(),
});

const auth = useAuth();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();

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
async function setReadonlySelected(projects: PentestProject[]) {
  await bulkAction(projects, p => projectStore.setReadonly(p, false), p => `Failed to activate "${p.name}"`);
  await listViewRef.value?.refresh();
}
</script>

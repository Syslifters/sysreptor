<template>
  <file-drop-area @drop="importBtnRef?.performImport($event)" class="h-100">
    <list-view 
      ref="listViewRef"
      url="/api/v1/projecttypes/?scope=global"
      v-model:ordering="localSettings.designListOrdering"
      :ordering-options="[
        {id: 'name', title: 'Name', value: 'name'},
        {id: 'created', title: 'Created', value: '-created'},
        {id: 'updated', title: 'Updated', value: '-updated'},
      ]"
      v-model:pinned-filters="localSettings.designListPinnedFilters"
      :filter-properties="filterProperties"
      :selectable="true"
    >
      <template #title>Designs</template>
      <template #navigation>
        <design-navigation-dropdown value="global" />
      </template>
      <template #actions="{ selectedItems }: { selectedItems: ProjectType[] }">
        <v-divider vertical />
        <design-create-design-dialog :project-type-scope="ProjectTypeScope.GLOBAL" data-testid="add-design-button"/>
        <design-import-design-dialog ref="importBtnRef" :project-type-scope="ProjectTypeScope.GLOBAL" data-testid="import-design" />
        <template v-if="selectedItems.length > 0">
          <v-divider vertical />
          <btn-export
            export-url="/api/v1/projecttypes/export/"
            :options="{ids: selectedItems.map(p => p.id)}"
            name="designs"
            extension=".tar.gz"
            button-variant="icon"
            variant="flat"
            density="comfortable"
          />
          <permission-info :value="auth.permissions.value.designer" permission-name="Designer">
            <btn-delete
              :delete="() => performDeleteSelected(selectedItems)"
              :disabled="!auth.permissions.value.designer"
              :confirm-input="`delete ${selectedItems.length} designs`"
              tooltip-text="Delete selected"
              icon="mdi-delete"
              density="comfortable"
            >
              <template #dialog-text>
                <p class="mt-0">
                  Do you really want to delete {{ selectedItems.length }} designs?
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
      <template #item="{item}: {item: ProjectType}">
        <design-list-item 
          :item="item" 
          :action-buttons="true" 
          :selectable="true"
          @filter="listViewRef?.addFilter($event)" 
        />
      </template>
    </list-view>
  </file-drop-area>
</template>

<script setup lang="ts">
import { ProjectTypeScope, type ProjectType } from '#imports';

definePageMeta({
  title: 'Designs',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => designListBreadcrumbs(),
});

const auth = useAuth();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const projectTypeStore = useProjectTypeStore();

const importBtnRef = useTemplateRef('importBtnRef');

const listViewRef = useTemplateRef('listViewRef');
const statusOptions = computed(() => apiSettings.settings?.statuses?.map(status => ({title: status.label, value: status.id, icon: status.icon})) || []);
const suggestedTags = useProjectTypeTags();
const filterProperties = computed((): FilterProperties[] => [
  { id: 'status', name: 'Status', icon: 'mdi-flag', type: 'select', options: statusOptions.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'combobox', options: suggestedTags.getTags, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'timerange', name: 'Time Created', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
  { id: 'language', name: 'Language', icon: 'mdi-translate', type: 'select', options: apiSettings.settings!.languages.map(l => l.code), allow_exclude: true, default: '', multiple: true },
]);

async function performDeleteSelected(projectTypes: ProjectType[]) {
  await bulkAction(projectTypes, projectTypeStore.delete, p => `Failed to delete design "${p.name}"`);
  await listViewRef.value?.refresh();
}
</script>

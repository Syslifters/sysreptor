<template>
  <file-drop-area @drop="importBtnRef?.performImport($event)" class="h-100">
    <list-view 
      ref="listViewRef"
      url="/api/v1/projecttypes/?scope=global"
      v-model:ordering="localSettings.designListOrdering"
      v-model:pinnedFilters="localSettings.designListPinnedFilters"
      :ordering-options="[
        {id: 'name', title: 'Name', value: 'name'},
        {id: 'created', title: 'Created', value: '-created'},
        {id: 'updated', title: 'Updated', value: '-updated'},
      ]"
      :filter-properties="filterProperties"
    >
      <template #title>Designs</template>
      <template #actions>
        <design-create-design-dialog :project-type-scope="ProjectTypeScope.GLOBAL" data-testid="add-design-button"/>
        <design-import-design-dialog ref="importBtnRef" :project-type-scope="ProjectTypeScope.GLOBAL" data-testid="import-design" />
      </template>
      <template #tabs v-if="apiSettings.settings!.features.private_designs">
        <v-tab :to="{ path: '/designs/', query: route.query }" exact prepend-icon="mdi-earth" text="Global" />
        <v-tab :to="{ path: '/designs/private/', query: route.query }" prepend-icon="mdi-account" text="Private" />
      </template>
      <template #item="{item}: {item: ProjectType}">
        <design-list-item :item="item" :action-buttons="true" @filter="listViewRef?.addFilter($event)" />
      </template>
    </list-view>
  </file-drop-area>
</template>

<script setup lang="ts">
import { ProjectTypeScope, type ProjectType } from '#imports';
import { sortBy, uniq } from 'lodash-es';

definePageMeta({
  title: 'Designs',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => designListBreadcrumbs(),
});

const route = useRoute();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();

const importBtnRef = useTemplateRef('importBtnRef');

const listViewRef = useTemplateRef('listViewRef');
const statusOptions = computed(() => apiSettings.settings?.statuses?.map(status => ({title: status.label, value: status.id, icon: status.icon})) || []);
const suggestedTags = ref<string[]>([]);
watch(() => listViewRef.value?.items?.data.value as ProjectType[]|undefined, (items) => {
  if (!items) { return; }
  suggestedTags.value = sortBy(uniq(items.flatMap(p => p.tags).concat(suggestedTags.value)));
}, { immediate: true, deep: 1 });
const filterProperties = computed((): FilterProperties[] => [
  { id: 'status', name: 'Status', icon: 'mdi-flag', type: 'select', options: statusOptions.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'combobox', options: suggestedTags.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'timerange', name: 'Time Created', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
  { id: 'language', name: 'Language', icon: 'mdi-translate', type: 'select', options: apiSettings.settings!.languages.map(l => l.code), allow_exclude: true, default: '', multiple: true },
]);
</script>

<template>
  <file-drop-area @drop="importBtnRef?.performImport($event)" class="h-100">
    <list-view 
      ref="listViewRef" 
      url="/api/v1/findingtemplates/"
      v-model:ordering="localSettings.templateListOrdering"
      :ordering-options="[
        {id: 'risk', title: 'Severity', value: '-risk'},
        {id: 'created', title: 'Created', value: '-created'},
        {id: 'updated', title: 'Updated', value: '-updated'},
      ]"
      :filter-properties="filterProperties"
    >
      <template #title>Templates</template>
      <template #actions>
        <permission-info :value="auth.permissions.value.template_editor" permission-name="Template Editor">
          <btn-create 
            @click="performCreate"
            :disabled="!auth.permissions.value.template_editor"
            :loading="performCreateInProgress"
          />
        </permission-info>
        <permission-info :value="auth.permissions.value.template_editor" permission-name="Template Editor">
          <btn-import 
            ref="importBtnRef"
            data-testid="import-templates"
            :import="performImport"
            :disabled="!auth.permissions.value.template_editor"
          />
        </permission-info>
      </template>
      <template #item="{item}: {item: FindingTemplate}">
        <template-list-item
          :template="item"
          :language="currentLanguage"
          :to="{path: `/templates/${item.id}/`, query: {language: currentLanguage}}"
          lines="two"
          @filter="listViewRef?.addFilter($event)"
        />
      </template>
    </list-view>
  </file-drop-area>
</template>

<script setup lang="ts">
import { sortBy, uniq, capitalize } from 'lodash-es';

definePageMeta({
  title: 'Templates',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => templateListBreadcrumbs(),
});

const route = useRoute();
const router = useRouter();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const auth = useAuth();
const templateStore = useTemplateStore();

const listViewRef = useTemplateRef('listViewRef');

const currentLanguage = computed({
  get: () => (Array.isArray(route.query.language) ? route.query.language[0] : route.query.language) || null,
  set: (val) => {
    router.replace({ query: { ...route.query, language: val || '' } })
  }
});

const importBtnRef = useTemplateRef('importBtnRef');
async function performImport(file: File) {
  const templates = await uploadFileHelper<FindingTemplate[]>('/api/v1/findingtemplates/import/', file);
  await navigateTo(`/templates/${templates[0]!.id}/`)
}

const performCreateInProgress = ref(false);
async function performCreate() {
  try {
    performCreateInProgress.value = true;
    const obj = await templateStore.create({
      tags: [],
      translations: [{
        is_main: true,
        language: apiSettings.settings!.languages?.[0]?.code || 'en-US',
        status: ReviewStatus.IN_PROGRESS,
        data: {
          title: 'TODO: New Template Title',
        },
      }],
    });
    await navigateTo(`/templates/${obj.id}/`);
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    performCreateInProgress.value = false;
  }
}

const statusOptions = computed(() => apiSettings.settings?.statuses?.map(status => ({title: status.label, value: status.id, icon: status.icon})) || []);
const languageOptions = computed(() => apiSettings.settings!.languages.map(l => ({title: l.name, value: l.code, icon: 'mdi-translate'})));
const riskLevelOptions = computed(() => Object.values(RiskLevel).map(l => ({title: capitalize(l), value: l})));
const suggestedTags = ref<string[]>([]);
watch(() => listViewRef.value?.items?.data.value as FindingTemplate[]|undefined, (items) => {
  if (!items) { return; }
  suggestedTags.value = sortBy(uniq(items.flatMap(p => p.tags).concat(suggestedTags.value)));
}, { immediate: true, deep: 1 });
const filterProperties = computed((): FilterProperties[] => [
  { id: 'status', name: 'Status', icon: 'mdi-flag', type: 'select', options: statusOptions.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'risk_level', name: 'Risk Level', icon: 'mdi-alert', type: 'select', options: riskLevelOptions.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'combobox', options: suggestedTags.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'timerange', name: 'Time Created', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
  { id: 'language', name: 'Language', icon: 'mdi-translate', type: 'select', options: languageOptions.value, allow_exclude: true, default: '', multiple: true },
]);
</script>

<template>
  <s-dialog v-model="dialogVisible" width="60%" max-width="60%" data-testid="create-finding-dialog">
    <template #title>New Finding</template>
    <template #default>
      <v-card-text>
        <v-row density="compact">
          <v-col cols="12" lg="9">
            <s-combobox
              ref="comboboxRef"
              :model-value="selectedTemplates"
              @update:model-value="selectedTemplates = ($event || []).filter((v: any) => v && typeof v === 'object' && 'id' in v)"
              @update:search="(v: string|null) => templates.search.value = v || ''"
              label="Template (optional)"
              :items="templates.data.value"
              item-value="id"
              :item-title="(t: FindingTemplate|string|null) => typeof t === 'string' ? t : ''"
              :hide-no-data="false"
              :clear-on-select="false"
              :menu-props="{ width: '50%' }"
              no-filter
              multiple
              return-object
              autofocus
              spellcheck="false"
              class="template-select"
              :class="{'hide-input': selectedTemplates.length > 0}"
            >
              <template #selection="{ item: template }">
                <div class="d-flex flex-row w-100">
                  <template-select-item :template="template as any" :language="displayLanguage" />
                  <s-btn-icon
                    icon="$delete"
                    @click.stop="removeSelectedTemplate(template as any)"
                    @mousedown.stop
                    v-tooltip.top="'Remove'"
                  />
                </div>
              </template>
              <template #item="{item: template, props: itemProps}">
                <v-list-item v-bind="itemProps" title="">
                  <template #prepend="{ isSelected }">
                    <v-checkbox-btn :model-value="isSelected" />
                  </template>
                  <template-select-item :template="template" :language="displayLanguage" />
                </v-list-item>
              </template>

              <template #no-data v-if="templates.data.value.length === 0 && templates.hasNextPage.value">
                <page-loader :items="templates" data-testid="page-loader" />
              </template>
              <template #append-item v-if="templates.data.value.length > 0">
                <page-loader :items="templates" data-testid="page-loader" />
              </template>
            </s-combobox>
          </v-col>
          <v-col cols="12" md="3">
            <s-language-selection
              v-model="templateLanguage"
              :items="templateLanguageChoices"
              :disabled="selectedTemplates.length === 0 || templateLanguageChoices.length === 0"
            />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <s-btn-other
          @click="dialogVisible = false"
          text="Cancel"
        />
        <s-btn-primary
          v-if="selectedTemplates.length > 0"
          @click="createFindingsFromTemplates"
          :loading="actionInProgress"
          :text="`Create from Templates (${selectedTemplates.length})`"
        >
          <span v-if="selectedTemplates.length === 1">Create from Template</span>
          <span v-else>Create from Templates ({{ selectedTemplates.length }})</span>
        </s-btn-primary>
        <s-btn-primary
          v-else @click="createEmptyFinding"
          :loading="actionInProgress"
          text="Create Empty Finding"
        />
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
import { uniq } from 'lodash-es';

const props = defineProps<{
  project: PentestProject;
}>();

const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const dialogVisible = ref(false);
const actionInProgress = ref(false);

const comboboxRef = useTemplateRef('comboboxRef');
const templates = useSearchableCursorPaginationFetcher({
  baseURL: '/api/v1/findingtemplates/',
  query: {
    ordering: '-usage',
    preferred_language: props.project.language
  }
});
const selectedTemplates = ref<FindingTemplate[]>([]);
const findingData = ref<Partial<PentestFinding>|null>();
watch(dialogVisible, () => {
  // Reset dialog
  templates.applyFilters({ search: '' }, { fetchInitialPage: false });
  if (comboboxRef.value) {
    comboboxRef.value.search = '';
  }
  selectedTemplates.value = [];
  findingData.value = null;
}, { flush: 'sync' });

const templateLanguage = ref<string|null>(null);
const templateLanguageChoices = computed(() => 
  uniq(selectedTemplates.value.flatMap(t => t.translations.map(tr => tr.language)))
  .map(code => apiSettings.settings!.languages.find(l => l.code === code)!)
  .filter(Boolean)
);
const displayLanguage = computed(() => templateLanguage.value || props.project.language);

watch(selectedTemplates, (newTemplates, oldTemplates) => {
  // Clear search when selecting/deselecting templates
  if (comboboxRef.value && (newTemplates.length > 0 || oldTemplates.length !== newTemplates.length)) {
    comboboxRef.value.search = '';
    templates.search.value = '';
  }
  
  // Prefill language selection
  if (templateLanguageChoices.value.length === 0) {
    templateLanguage.value = null;
  } else if (templateLanguageChoices.value.some(l => l.code === templateLanguage.value)) {
    // Keep current templateLanguage
  } else if (templateLanguageChoices.value.some(l => l.code === props.project.language)) {
    // Use project language
    templateLanguage.value = props.project.language;
  } else {
    // Use first template language
    templateLanguage.value = selectedTemplates.value[0]?.translations.find(tr => tr.is_main)?.language || templateLanguageChoices.value[0]?.code || null;
  }
}, { deep: 1 });

function removeSelectedTemplate(template: FindingTemplate) {
  selectedTemplates.value = selectedTemplates.value.filter(t => t.id !== template.id);
}

async function createEmptyFinding() {
  try {
    actionInProgress.value = true;
    const title = comboboxRef.value?.search?.trim() || null;
    const finding = await projectStore.createFinding(props.project, {
      ...(findingData.value || {}),
      data: {
        ...(findingData.value?.data || {}),
        ...(title ? { title } : {}) 
      }
    });
    await navigateTo(`/projects/${finding.project}/reporting/findings/${finding.id}/`)
    dialogVisible.value = false;
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    actionInProgress.value = false;
  }
}
async function createFindingsFromTemplates() {
  try {
    actionInProgress.value = true;
    let created = await bulkAction(selectedTemplates.value, t => projectStore.createFindingFromTemplate(props.project, {
      ...(findingData.value || {}),
      template: t.id,
      template_language: 
        t.translations.find(tr => tr.language === templateLanguage.value)?.language || 
        t.translations.find(tr => tr.language === props.project.language)?.language || 
        t.translations.find(tr => tr.is_main)?.language || 
        '',
    }), t => `Failed to create finding from template "${t.translations.find(tr => tr.is_main)?.data.title || t.id}"`)
    
    created = created.filter(Boolean);
    if (created.length > 0) {
      if (created.length > 1) {
        successToast(`Created ${created.length} finding${created.length === 1 ? '' : 's'}`);
      }
      await navigateTo(`/projects/${created[0]!.project}/reporting/findings/${created[0]!.id}/`)
      dialogVisible.value = false;
    }
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    actionInProgress.value = false;
  }
}

defineExpose({
  open: (data?: Partial<PentestFinding>|null) => { 
    dialogVisible.value = true 
    findingData.value = data || null;
  },
});
</script>

<style lang="scss" scoped>
.template-select {
  :deep() {
    .v-field__input {
      width: 100%;
    }

    .v-combobox__selection {
      max-width: 100%;
    }

    .v-chip__content {
      overflow: visible;
    }

    .v-field__input {
      max-height: 15em;
      overflow-y: auto;
    }
  }

  &.hide-input:deep() {
    input {
      height: 0;
      width: 0;
    }
    .v-combobox__selection {
      opacity: 1;
      height: auto;
      width: 100%;
    }
  }
  &:not(.hide-input):deep() {
    input {
      opacity: 1;
    }
  }
}
</style>

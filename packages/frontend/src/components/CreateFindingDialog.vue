<template>
  <s-dialog v-model="dialogVisible" width="60%" max-width="60%" data-testid="create-finding-dialog">
    <template #title>New Finding</template>
    <template #default>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="9">
            <s-combobox
              v-model="searchInput"
              @update:search="(v: string|null) => templates.search.value = v || ''"
              label="Template (optional)"
              :items="templates.data.value"
              item-value="id"
              :item-title="(t: FindingTemplate|string|null) => typeof t === 'string' ? t : ''"
              :hide-no-data="false"
              :menu-props="{ width: '50%' }"
              no-filter
              clearable
              return-object
              autofocus
              spellcheck="false"
              class="template-select"
              :class="{'hide-input': !!currentTemplate}"
              @keydown="onKeydown"
            >
              <template #selection="{ item: { raw: template }}">
                <template-select-item v-if="template?.id" :template="template" :language="displayLanguage" />
                <template v-else>{{ searchInput }}</template>
              </template>
              <template #item="{item: { raw: template}, props: itemProps}">
                <v-list-item v-bind="itemProps" title="">
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
              :disabled="!currentTemplate"
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
          v-if="currentTemplate?.id"
          @click="createFindingFromTemplate"
          :loading="actionInProgress"
          text="Create from Template"
        />
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
const props = defineProps<{
  project: PentestProject;
}>();

const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const dialogVisible = ref(false);
const actionInProgress = ref(false);

const templates = useSearchableCursorPaginationFetcher({
  baseURL: '/api/v1/findingtemplates/',
  query: {
    ordering: '-usage',
    preferred_language: props.project.language
  }
});
const searchInput = ref<FindingTemplate|string|null>(null);
const currentTemplate = computed<FindingTemplate|null>(() => typeof searchInput.value === "string" ? null : searchInput.value);
const findingData = ref<Partial<PentestFinding>|null>();
watch(dialogVisible, () => {
  // Reset dialog
  templates.applyFilters({ search: '' }, { fetchInitialPage: false });
  searchInput.value = null;
  findingData.value = null;
}, { flush: 'sync' });

const templateLanguage = ref<string|null>(null);
const templateLanguageChoices = computed(() => currentTemplate.value?.translations?.map(tr => apiSettings.settings!.languages.find(l => l.code === tr.language)!) || []);
const displayLanguage = computed(() => templateLanguage.value || props.project.language);
watch(currentTemplate, () => {
  if (!currentTemplate.value) {
    templateLanguage.value = null;
  } else if (currentTemplate.value.translations.some(tr => tr.language === templateLanguage.value)) {
    // Keep current templateLanguage
  } else if (currentTemplate.value.translations.some(tr => tr.language === props.project.language)) {
    templateLanguage.value = props.project.language;
  } else {
    templateLanguage.value = currentTemplate.value.translations.find(tr => tr.is_main)!.language;
  }
});

async function createEmptyFinding() {
  try {
    actionInProgress.value = true;
    const title = ((typeof searchInput.value === "string") ? searchInput.value : null);
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
async function createFindingFromTemplate() {
  try {
    actionInProgress.value = true;
    const finding = await projectStore.createFindingFromTemplate(props.project, {
      ...(findingData.value || {}),
      template: currentTemplate.value!.id,
      template_language: templateLanguage.value!,
    });
    await navigateTo(`/projects/${finding.project}/reporting/findings/${finding.id}/`)
    dialogVisible.value = false;
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    actionInProgress.value = false;
  }
}

function onKeydown(event: KeyboardEvent) {
  if (['Backspace', 'Delete'].includes(event.key) && currentTemplate.value) {
    searchInput.value = null;
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
  }

  &.hide-input:deep() {
    input {
      height: 0;
      width: 0;
    }
    .v-combobox__selection {
      opacity: 1;
      height: auto;
    }
  }
  &:not(.hide-input):deep() {
    input {
      opacity: 1;
    }
  }
}
</style>

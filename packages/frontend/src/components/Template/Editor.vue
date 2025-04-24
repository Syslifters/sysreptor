<template>
  <div v-if="fieldDefinitionTitle" :key="template.id" class="h-100 d-flex flex-column">
    <edit-toolbar v-bind="props.toolbarAttrs || {}" ref="toolbarRef">
      <template #title>
        <v-tabs v-model="currentTranslationLanguage"  center-active>
          <v-tab 
            v-for="tr in template.translations" 
            :key="tr.id"
            :value="tr.language"
          >
            <v-icon size="small" start icon="mdi-translate" />
            {{ languageInfo(tr.language).name }}
            <btn-delete
              v-if="!tr.is_main"
              :disabled="props.readonly"
              :delete="() => deleteTranslation(tr.id)"
              button-variant="icon"
            />
          </v-tab>

          <s-btn-icon
            v-if="unusedLanguageInfos.length > 0"
            :disabled="props.readonly"
          >
            <v-icon icon="mdi-plus" />
            <s-tooltip activator="parent" text="Add translation" />
            <v-menu activator="parent" location="bottom" class="menu-max-height">
              <v-list>
                <v-list-item v-for="lang in unusedLanguageInfos" :key="lang.code" link @click="createTranslation(lang.code)">
                  <template #prepend> <v-icon size="small" start icon="mdi-translate" /></template>
                  <template #title>{{ lang.name }}</template>
                </v-list-item>
              </v-list>
            </v-menu>
          </s-btn-icon>
        </v-tabs>
      </template>

      <slot name="toolbar-actions" />

      <btn-history v-if="props.history" v-model="historyVisible" />

      <template #context-menu v-if="$slots['toolbar-context-menu']">
        <slot name="toolbar-context-menu" />
      </template>
    </edit-toolbar>

    <history-timeline-template
      v-if="props.history"
      v-model="historyVisible"
      :template="template"
      :translation="currentTranslation"
      :current-url="`/templates/${template.id}/?language=${currentTranslation.language}`"
    />
    
    <v-window v-model="currentTranslationLanguage" class="flex-grow-height">
      <v-window-item 
        v-for="translation in template.translations" 
        :key="translation.id" 
        :value="translation.language" 
        class="h-100"
      >
        <v-container fluid class="pt-0 h-100 overflow-y-auto">
          <dynamic-input-field
            v-model="translation.data.title"
            :id="fieldDefinitionTitle.id"
            :definition="fieldDefinitionTitle"
            :lang="translation.language"
            v-bind="fieldAttrs"
            :data-testid="`title-${translation.language}`"
          />

          <s-status-selection
            v-model="translation.status"
            :readonly="props.readonly"
            variant="outlined"
            density="default"
            class="mt-4"
            data-testid="template-status"
          />
          <s-tags
            v-model="template.tags"
            :items="templateTagSuggestions"
            :readonly="props.readonly"
            class="mt-4"
          />
          <s-language-selection
            :model-value="translation.language"
            @update:model-value="translation.language = currentTranslationLanguage = $event"
            :items="[currentLanguageInfo].concat(unusedLanguageInfos)"
            :readonly="props.readonly"
            class="mt-4"
          />

          <div v-for="d in visibleFieldDefinitionsExceptTitle" :key="d.id" class="d-flex flex-row">
            <dynamic-input-field
              :model-value="(d.id in translation.data) ? translation.data[d.id] : mainTranslation.data[d.id]"
              @update:model-value="translation.data[d.id] = $event"
              :id="d.id"
              :definition="d"
              :lang="translation.language"
              :disabled="!translation.is_main && !(d.id in translation.data)"
              v-bind="fieldAttrs"
            />
            <div v-if="!translation.is_main" class="mt-4 ml-1">
              <s-btn-secondary
                v-if="d.id in translation.data"
                @click="translateFieldReset(translation, d.id)"
                :disabled="props.readonly"
                class="h-100"
                size="small"
              >
                <v-icon size="small" icon="mdi-pencil-off" />
                <s-tooltip activator="parent">
                  Reset field to inherit text from the main language {{ mainLanguageInfo.name }}.
                  Currently it is overridden for the {{ currentLanguageInfo.name }} translation.<br>
                </s-tooltip>
              </s-btn-secondary>
              <s-btn-secondary
                v-else
                @click="translateFieldCopy(translation, d.id)"
                :disabled="props.readonly"
                class="h-100"
                size="small"
              >
                <v-icon size="small" icon="mdi-pencil" />
                <s-tooltip activator="parent">
                  Override field in {{ currentLanguageInfo.name }} translation.<br>
                  Currently it is inherited from the main language {{ mainLanguageInfo.name }}.
                </s-tooltip>
              </s-btn-secondary>
            </div>
          </div>
        </v-container>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import type { FindingTemplate, FindingTemplateTranslation, MarkdownEditorMode } from "#imports";
import { uuidv4 } from "@base/utils/helpers";
import { cloneDeep } from "lodash-es";

const props = defineProps<{
  modelValue: FindingTemplate;  // Reactive object expected
  fieldDefinitionList?: TemplateFieldDefinition[];
  initialLanguage?: string|null;
  readonly?: boolean;
  toolbarAttrs?: object;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrlMap?: Record<string, string>;
  history?: boolean;
}>();

const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const templateStore = useTemplateStore();
useLazyAsyncData(async () => await templateStore.getFieldDefinition());

const template = computed(() => props.modelValue);
const mainTranslation = computed(() => template.value.translations.find(tr => tr.is_main)!);

const toolbarRef = useTemplateRef('toolbarRef');
const currentTranslationLanguage = ref((template.value.translations.find(tr => tr.language === props.initialLanguage) || mainTranslation.value).language);
const currentTranslation = computed(() => template.value.translations.find(tr => tr.language === currentTranslationLanguage.value) || mainTranslation.value);
watch(() => template.value.translations, () => {
  if (!template.value.translations.find(tr => tr.language === currentTranslationLanguage.value)) {
    currentTranslationLanguage.value = mainTranslation.value.language;
  }
}, { deep: 1 });

const restoreTranslationDataCache = ref<Record<string, Record<string, any>>>({});
const initialLanguages = ref(template.value.translations.map(tr => tr.language));
const historyVisible = ref(false);
const templateTagSuggestions = [
  'web', 'infrastructure', 'organizational', 'hardening', 'internal', 'external', 'third_party',
  'active_directory', 'windows', 'client',
  'config', 'update', 'development', 'crypto',
];

const visibleFieldDefinitions = computed(() => (props.fieldDefinitionList || templateStore.fieldDefinitionList).filter(f => f.visible));
const visibleFieldDefinitionsExceptTitle = computed(() => visibleFieldDefinitions.value.filter(f => f.id !== 'title'));
const fieldDefinitionTitle = computed(() => (props.fieldDefinitionList || templateStore.fieldDefinitionList).find(f => f.id === 'title')!);

function languageInfo(languageCode: string) {
  return apiSettings.settings!.languages.find(l => l.code === languageCode) || { code: '??-??', name: 'Unknown' } as Language;
}
const availableLanguageInfos = computed(() => apiSettings.settings!.languages.filter(l => l.enabled || initialLanguages.value.includes(l.code)));
const unusedLanguageInfos = computed(() => availableLanguageInfos.value.filter(l => !template.value.translations.some(tr => tr.language === l.code)));
const currentLanguageInfo = computed(() => languageInfo(currentTranslation.value.language));
const mainLanguageInfo = computed(() => languageInfo(mainTranslation.value.language));


function translateFieldCopy(translation: FindingTemplateTranslation, fieldId: string) {
  // Restore previous value or copy field from main translation
  const restoreValue = cloneDeep(toValue(restoreTranslationDataCache.value[translation.id]?.[fieldId] || mainTranslation.value.data[fieldId]));
  translation.data[fieldId] = restoreValue !== undefined ? restoreValue : null;
}
function translateFieldReset(translation: FindingTemplateTranslation, fieldId: string) {
  // Store old content in cache to be able to restore value
  if (!restoreTranslationDataCache.value[translation.id]) {
    restoreTranslationDataCache.value[translation.id] = {};
  }
  restoreTranslationDataCache.value[translation.id]![fieldId] = cloneDeep(toValue(translation.data[fieldId]));
  // Remove field from translation (uses value from main translation)
  delete translation.data[fieldId];
}

async function createTranslation(language: string) {
  const translation = {
    id: uuidv4(),
    language,
    status: ReviewStatus.IN_PROGRESS,
    is_main: false,
    data: {
      title: mainTranslation.value.data.title,
    },
  } as Partial<FindingTemplateTranslation> as FindingTemplateTranslation;
  template.value.translations.push(translation);
  currentTranslationLanguage.value = language;
}
function deleteTranslation(translationId: string) {
  template.value.translations.splice(
    template.value.translations.findIndex(tr => tr.id === translationId),
    1
  );
}

const fieldAttrs = computed(() => ({
  readonly: props.readonly,
  selectableUsers: [],
  spellcheckEnabled: localSettings.templateSpellcheckEnabled,
  'onUpdate:spellcheckEnabled': (value: boolean) => { localSettings.templateSpellcheckEnabled = value },
  markdownEditorMode: localSettings.templateMarkdownEditorMode,
  'onUpdate:markdownEditorMode': (value: MarkdownEditorMode) => { localSettings.templateMarkdownEditorMode = value },
  uploadFile: props.uploadFile,
  rewriteFileUrlMap: props.rewriteFileUrlMap,
}))

defineExpose({
  toolbarRef,
});
</script>

<style lang="scss" scoped>
.menu-max-height {
  max-height: 40vh;
}

:deep(.v-window__container) {
  height: 100%;
}
</style>

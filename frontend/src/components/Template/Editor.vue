<template>
  <div v-if="fieldDefinitionTitle" :key="template.id" class="mb-4">
    <edit-toolbar v-bind="toolbarAttrs" ref="toolbarRef">
      <template #title>
        <v-tabs v-model="currentTab" center-active>
          <v-tab v-for="tr in template.translations" :key="tr.id">
            <v-icon size="small" start icon="mdi-translate" />
            {{ languageInfo(tr.language).name }}
            <btn-delete
              v-if="!tr.is_main"
              :disabled="props.readonly"
              :delete="() => deleteTranslation(tr.id)"
              button-variant="icon"
            />
          </v-tab>

          <s-btn
            v-if="unusedLanguageInfos.length > 0"
            :disabled="props.readonly"
            icon
            variant="text"
          >
            <v-icon icon="mdi-plus" />
            <s-tooltip activator="parent" text="Add translation" />
            <v-menu activator="parent" location="bottom" class="menu-max-height">
              <v-list>
                <v-list-item v-for="lang in unusedLanguageInfos" :key="lang.code" link @click="createTranslation(lang.code)">
                  <template #prepend> <v-icon size="small" start icon="mdi-translate" /></template>
                  <template #title>{{ lang.name }} ({{ lang.code }})</template>
                </v-list-item>
              </v-list>
            </v-menu>
          </s-btn>
        </v-tabs>
      </template>

      <slot name="toolbar-actions" />

      <s-btn
        v-if="history"
        @click="historyVisible = !historyVisible"
        color="secondary"
        prepend-icon="mdi-history"
      >
        <span class="d-none d-lg-inline">Version History</span>
      </s-btn>

      <template #context-menu v-if="$slots['toolbar-context-menu']">
        <slot name="toolbar-context-menu" />
      </template>
    </edit-toolbar>

    <template-history-timeline
      v-if="history"
      v-model="historyVisible"
      :template="template"
      :translation="currentTranslation"
      :current-url="`/templates/${template.id}/?language=${currentTranslation.language}`"
    />

    <v-window v-model="currentTab">
      <v-window-item v-for="(translation, idx) in template.translations" :key="idx">
        <dynamic-input-field
          :model-value="translation.data.title"
          @update:model-value="(v: string) => updateTranslationData(translation, fieldDefinitionTitle.id, v)"
          :id="fieldDefinitionTitle.id"
          :definition="fieldDefinitionTitle"
          :selectable-users="[]"
          :lang="translation.language"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :disabled="props.readonly"
        />

        <s-status-selection
          :model-value="translation.status"
          @update:model-value="(v: any) => updateTranslationField(translation, 'status', v)"
          :disabled="props.readonly"
          variant="outlined"
          density="default"
          class="mt-4"
        />
        <s-tags
          :model-value="template.tags"
          @update:model-value="(v: string[]) => updateTemplateField('tags', v)"
          :items="templateTagSuggestions"
          :disabled="props.readonly"
          class="mt-4"
        />
        <s-language-selection
          :model-value="translation.language"
          @update:model-value="(v: string) => updateTranslationField(translation, 'language', v)"
          :items="[currentLanguageInfo].concat(unusedLanguageInfos)"
          :disabled="props.readonly"
          class="mt-4"
        />

        <div v-for="d in visibleFieldDefinitionsExceptTitle" :key="d.id" class="d-flex flex-row">
          <dynamic-input-field
            :model-value="(d.id in translation.data) ? translation.data[d.id] : mainTranslation.data[d.id]"
            @update:model-value="(v: any) => updateTranslationData(translation, d.id, v)"
            :id="d.id"
            :definition="d"
            :selectable-users="[]"
            :lang="translation.language"
            :upload-file="uploadFile"
            :rewrite-file-url="rewriteFileUrl"
            :disabled="props.readonly || (!translation.is_main && !(d.id in translation.data))"
            class="flex-grow-width"
          />
          <div v-if="!translation.is_main" class="mt-4 ml-1">
            <s-btn
              v-if="d.id in translation.data"
              @click="translateFieldReset(translation, d.id)"
              :disabled="props.readonly"
              color="secondary"
              class="h-100"
              size="small"
            >
              <v-icon size="small" icon="mdi-pencil-off" />
              <s-tooltip activator="parent">
                Reset field to inherit text from the main language {{ mainLanguageInfo.name }}.
                Currently it is overridden for the {{ currentLanguageInfo.name }} translation.<br>
              </s-tooltip>
            </s-btn>
            <s-btn
              v-else
              @click="translateFieldCopy(translation, d.id)"
              :disabled="props.readonly"
              color="secondary"
              class="h-100"
              size="small"
            >
              <v-icon size="small" icon="mdi-pencil" />
              <s-tooltip activator="parent">
                Override field in {{ currentLanguageInfo.name }} translation.<br>
                Currently it is inherited from the main language {{ mainLanguageInfo.name }}.
              </s-tooltip>
            </s-btn>
          </div>
        </div>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import cloneDeep from "lodash/cloneDeep";
import { v4 as uuidv4 } from "uuid";

const props = withDefaults(defineProps<{
  modelValue: FindingTemplate;
  initialLanguage?: string|null;
  readonly?: boolean;
  toolbarAttrs?: Object;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrl?: (fileSrc: string) => string;
  history?: boolean;
}>(), {
  initialLanguage: null,
  toolbarAttrs: () => ({}),
  uploadFile: undefined,
  rewriteFileUrl: undefined,
  readonly: false,
  history: false,
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: FindingTemplate): void;
}>();

const templateStore = useTemplateStore();
const apiSettings = useApiSettings();
useLazyAsyncData(async () => await templateStore.getFieldDefinition());

const template = computed(() => props.modelValue);
const mainTranslation = computed(() => template.value.translations.find(tr => tr.is_main)!);

const toolbarRef = ref();
const currentTranslation = ref(template.value.translations.find(tr => tr.language === props.initialLanguage) || mainTranslation.value);
const currentTab = computed({
  get: () => template.value.translations.findIndex(tr => tr.id === currentTranslation.value.id),
  set: (idx) => { currentTranslation.value = template.value.translations[idx] || mainTranslation.value; },
})
watch(template, () => {
  currentTranslation.value = template.value.translations.find(tr => tr.id === currentTranslation.value.id) ||
      template.value.translations.find(tr => tr.language === currentTranslation.value.language) ||
      mainTranslation.value;
}, { deep: true });

const restoreTranslationDataCache = ref<{ [key: string]: { [key: string]: any } }>({});
const initialLanguages = ref(template.value.translations.map(tr => tr.language));
const historyVisible = ref(false);
const templateTagSuggestions = [
  'web', 'infrastructure', 'organizational', 'hardening', 'internal', 'external', 'third_party',
  'active_directory', 'windows', 'client',
  'config', 'update', 'development', 'crypto',
];

const visibleFieldDefinitions = computed(() => templateStore.fieldDefinitionList.filter(f => f.visible));
const visibleFieldDefinitionsExceptTitle = computed(() => visibleFieldDefinitions.value.filter(f => f.id !== 'title'));
const fieldDefinitionTitle = computed(() => templateStore.fieldDefinitionList.find(f => f.id === 'title')!);

function languageInfo(languageCode: string) {
  return apiSettings.settings!.languages.find(l => l.code === languageCode) || { code: '??-??', name: 'Unknown' };
}
const availableLanguageInfos = computed(() => apiSettings.settings!.languages.filter(l => l.enabled || initialLanguages.value.includes(l.code)));
const unusedLanguageInfos = computed(() => availableLanguageInfos.value.filter(l => !template.value.translations.some(tr => tr.language === l.code)));
const currentLanguageInfo = computed(() => languageInfo(currentTranslation.value.language));
const mainLanguageInfo = computed(() => languageInfo(mainTranslation.value.language));

function updateTemplateField(fieldId: string, value: any) {
  emit('update:modelValue', { ...template.value, [fieldId]: value });
}
function updateTranslationField(translation: FindingTemplateTranslation, fieldId: string, value: any) {
  updateTemplateField('translations', template.value.translations.map(tr =>
    tr.id === translation.id ? { ...tr, [fieldId]: value } : tr));
}
function updateTranslationData(translation: FindingTemplateTranslation, fieldId: string, value: any) {
  const data = Object.fromEntries(Object.entries(translation.data).filter(([k]) => k !== fieldId));
  if (value !== undefined) {
    data[fieldId] = value;
  }
  updateTranslationField(translation, 'data', data);
}

function translateFieldCopy(translation: FindingTemplateTranslation, fieldId: string) {
  // Restore previous value or copy field from main translation
  const restoreValue = restoreTranslationDataCache.value[translation.id]?.[fieldId] || cloneDeep(mainTranslation.value.data[fieldId]);
  updateTranslationData(translation, fieldId, restoreValue !== undefined ? restoreValue : null);
}
function translateFieldReset(translation: FindingTemplateTranslation, fieldId: string) {
  // Store old content in cache to be able to restore value
  if (!restoreTranslationDataCache.value[translation.id]) {
    restoreTranslationDataCache.value[translation.id] = {};
  }
  restoreTranslationDataCache.value[translation.id][fieldId] = translation.data[fieldId]
  // Remove field from translation (uses value from main translation)
  updateTranslationData(translation, fieldId, undefined);
}

async function createTranslation(language: string) {
  updateTemplateField('translations', [
    ...template.value.translations,
    {
      id: uuidv4(),
      language,
      status: 'in-progress',
      is_main: false,
      data: {
        title: mainTranslation.value.data.title,
      },
    }]);
  await nextTick();
  currentTranslation.value = template.value.translations.find(tr => tr.language === language) || currentTranslation.value;
}
function deleteTranslation(translationId: string) {
  updateTemplateField('translations', template.value.translations.filter(tr => tr.id !== translationId))
}

defineExpose({
  toolbarRef,
});
</script>

<style lang="scss" scoped>
.menu-max-height {
  max-height: 40vh;
}
</style>

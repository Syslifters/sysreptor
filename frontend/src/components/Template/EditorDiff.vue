<template>
  <div v-if="fieldDefinitionTitle" :key="template.id" class="h-100 d-flex flex-column">
    <edit-toolbar v-bind="toolbarAttrs" ref="toolbarRef">
      <template #title>
        <v-tabs v-model="currentTab" center-active>
          <v-tab v-for="tr in translationInfos" :key="tr.id">
            <v-icon size="small" start icon="mdi-translate" />
            {{ languageInfo(tr.language).name }}
          </v-tab>
        </v-tabs>
      </template>

      <slot name="toolbar-actions" />

      <btn-history v-model="historyVisible" />

      <template #context-menu v-if="$slots['toolbar-context-menu']">
        <slot name="toolbar-context-menu" />
      </template>
    </edit-toolbar>

    <history-timeline-template
      v-model="historyVisible"
      :template="template"
      :translation="currentTranslation"
      :current-url="`/templates/${template.id}/?language=${currentTranslation.language}`"
    />

    <v-window v-model="currentTab" class="flex-grow-height">
      <v-window-item v-for="(tr, idx) in translationInfos" :key="idx" class="h-100">
        <v-container fluid class="pt-0 h-100 overflow-y-auto">
          <v-row class="mt-0">
            <v-col cols="6" class="pb-0">
              <h2 class="text-h5 text-center">Historic Version <chip-date :value="props.historyDate" /></h2>
            </v-col>
            <v-col cols="6" class="pb-0">
              <h2 class="text-h5 text-center">Current Version</h2>
            </v-col>
          </v-row>

          <dynamic-input-field-diff
            v-bind="diffFieldAttrs(tr, fieldDefinitionTitle)"
          />
        
          <v-row class="mt-4" :class="{'diff-highlight-changed': tr.historic?.status !== tr.current?.status}">
            <v-col cols="6">
              <s-status-selection
                :model-value="tr.historic?.status"
                :disabled="true"
                variant="outlined"
                density="default"
              />
            </v-col>
            <v-col cols="6">
              <s-status-selection
                :model-value="tr.current?.status"
                :disabled="true"
                variant="outlined"
                density="default"
              />
            </v-col>
          </v-row>
          <v-row class="mt-4" :class="{'diff-highlight-changed': String(props.historic.value.tags) !== String(props.current.value.tags)}">
            <v-col cols="6">
              <s-tags
                :model-value="props.historic.value.tags"
                :disabled="true"
              />
            </v-col>
            <v-col cols="6">
              <s-tags
                :model-value="props.current.value.tags"
                :disabled="true"
              />
            </v-col>
          </v-row>
          <v-row class="mt-4" :class="{'diff-highlight-changed': tr.historic?.language !== tr.current?.language}">
            <v-col cols="6">
              <s-language-selection
                :model-value="tr.historic?.language"
                :disabled="true"
              />
            </v-col>
            <v-col cols="6">
              <s-language-selection
                :model-value="tr.current?.language"
                :disabled="true"
              />
            </v-col>
          </v-row>
        
          <div v-for="d in visibleFieldDefinitionsExceptTitle" :key="d.id">
            <dynamic-input-field-diff
              v-bind="diffFieldAttrs(tr, d)"
            />
          </div>
        </v-container>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import { MarkdownEditorMode } from "#imports";

const props = defineProps<{
  historic: {
    value: FindingTemplate;
    rewriteFileUrl?: (fileSrc: string) => string;
  },
  current: {
    value: FindingTemplate;
    rewriteFileUrl?: (fileSrc: string) => string;
  }
  initialLanguage?: string|null;
  toolbarAttrs?: object;
  fieldDefinitionList: TemplateFieldDefinition[];
  historyDate: string;
}>();

const apiSettings = useApiSettings();
const templateStore = useTemplateStore();
useLazyAsyncData(async () => await templateStore.getFieldDefinition());

const template = computed(() => props.historic.value);
const mainTranslation = computed(() => template.value.translations.find(tr => tr.is_main)!);

type TranslationDiffInfo = {
  id: string;
  language: string;
  historic?: FindingTemplateTranslation;
  current?: FindingTemplateTranslation;
}
const translationInfos = computed(() => {
  const out = [] as TranslationDiffInfo[];
  for (const tr of props.historic.value.translations.concat(props.current.value.translations)) {
    if (!out.find(trInfo => trInfo.id === tr.id)) {
      out.push({
        id: tr.id,
        language: tr.language,
        historic: props.historic.value.translations.find(trInfo => trInfo.id === tr.id),
        current: props.current.value.translations.find(trInfo => trInfo.id === tr.id),
      });
    }
  }
  return out;
})

const toolbarRef = ref();
const currentTranslation = ref(template.value.translations.find(tr => tr.language === props.initialLanguage) || mainTranslation.value);
const currentTab = computed({
  get: () => template.value.translations.findIndex(tr => tr.id === currentTranslation.value.id),
  set: (idx) => { currentTranslation.value = template.value.translations[idx] || mainTranslation.value; },
})

const historyVisible = ref(false);

const visibleFieldDefinitions = computed(() => props.fieldDefinitionList.filter(f => f.visible));
const visibleFieldDefinitionsExceptTitle = computed(() => visibleFieldDefinitions.value.filter(f => f.id !== 'title'));
const fieldDefinitionTitle = computed(() => props.fieldDefinitionList.find(f => f.id === 'title')!);

function languageInfo(languageCode: string) {
  return apiSettings.settings!.languages.find(l => l.code === languageCode) || { code: '??-??', name: 'Unknown' } as Language;
}

const markdownEditorMode = ref(MarkdownEditorMode.MARKDOWN);
watch(markdownEditorMode, (val) => { 
  if (val === MarkdownEditorMode.MARKDOWN_AND_PREVIEW) {
    markdownEditorMode.value = MarkdownEditorMode.PREVIEW;
  }
});

const diffFieldAttrs = computed(() => (translationInfo: TranslationDiffInfo, definition: FieldDefinition) => {
  const commonProps = {
    definition,
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (value: MarkdownEditorMode) => { markdownEditorMode.value = value },
    selectableUsers: [],
    readonly: true,
  };
  const mainTranslationCurrent = props.current.value.translations.find(tr => tr.is_main);
  return {
    id: definition.id,
    historic: {
      value: translationInfo.historic ? (
        (definition.id in translationInfo.historic.data) ? 
          translationInfo.historic!.data[definition.id] : 
          mainTranslation.value.data[definition.id]) :
        null,
      lang: translationInfo.historic?.language,
      rewriteFileUrl: props.historic.rewriteFileUrl,
      ...commonProps
    },
    current: {
      value: translationInfo.current ? (
        (definition.id in translationInfo.current.data) ? 
          translationInfo.current!.data[definition.id] : 
          mainTranslationCurrent!.data[definition.id]) :
        null,
      lang: translationInfo.current?.language,
      rewriteFileUrl: props.current.rewriteFileUrl,
      ...commonProps,
    },
  };
});
</script>

<style scoped lang="scss">
:deep(.v-window__container) {
  height: 100%;
}
</style>

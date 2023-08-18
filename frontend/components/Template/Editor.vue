<template>
  <div v-if="fieldDefinitionTitle" :key="template.id" class="mb-4">
    <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents">
      <template #title>
        <v-tabs v-model="currentTab" center-active>
          <v-tab v-for="tr in template.translations" :key="tr.id">
            <v-icon small left>mdi-translate</v-icon>
            {{ languageInfo(tr.language).name }}
            <btn-delete v-if="!tr.is_main" :disabled="readonly" :delete="() => deleteTranslation(tr.id)" icon />
          </v-tab>
                
          <s-tooltip v-if="unusedLanguageInfos.length > 0">
            <template #activator="{on: tooltipOn}">
              <v-menu bottom offset-y max-height="40vh">
                <template #activator="{attrs: menuAttrs, on: menuOn}">
                  <s-btn :disabled="readonly" icon v-bind="menuAttrs" v-on="{...tooltipOn, ...menuOn}">
                    <v-icon>mdi-plus</v-icon>
                  </s-btn>
                </template>

                <v-list>
                  <v-list-item v-for="lang in unusedLanguageInfos" :key="lang.code" link @click="createTranslation(lang.code)">
                    <v-list-item-title>
                      <v-icon small left>mdi-translate</v-icon>
                      {{ lang.name }} ({{ lang.code }})
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </template>
            <template #default>
              Add translation
            </template>
          </s-tooltip>
        </v-tabs>
      </template>

      <template #context-menu v-if="$slots['toolbar-actions']">
        <slot name="toolbar-actions" />
      </template>
    </edit-toolbar>

    <v-tabs-items v-model="currentTab">
      <v-tab-item v-for="translation, idx in template.translations" :key="idx">
        <dynamic-input-field 
          :value="translation.data.title"
          @input="v => updateTranslationData(translation, fieldDefinitionTitle.id, v)"
          v-model="translation.data.title"
          :id="fieldDefinitionTitle.id" 
          :definition="fieldDefinitionTitle" 
          :selectable-users="[]" 
          :lang="translation.language"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :disabled="readonly"
        />

        <status-selection 
          :value="translation.status"
          @input="v => updateTranslationField(translation, 'status', v)"
          :disabled="readonly" 
          outlined 
        />
        <s-tags 
          :value="template.tags"
          @input="v => updateTemplateField('tags', v)"
          :items="templateTagSuggestions" 
          :disabled="readonly" 
        />
        <language-selection 
          :value="translation.language"
          @input="v => updateTranslationField(translation, 'language', v)"
          :items="[currentLanguageInfo].concat(unusedLanguageInfos)" 
          :disabled="readonly" 
          class="mt-4"
        />

        <div v-for="d in visibleFieldDefinitionsExceptTitle" :key="d.id" class="d-flex flex-row">
          <dynamic-input-field 
            :value="(d.id in translation.data) ? translation.data[d.id] : mainTranslation.data[d.id]"
            @input="v => updateTranslationData(translation, d.id, v)" 
            :id="d.id" 
            :definition="d" 
            :selectable-users="[]" 
            :lang="translation.language"
            :upload-file="uploadFile"
            :rewrite-file-url="rewriteFileUrl"
            :disabled="readonly || (!translation.is_main && !(d.id in translation.data))"
            class="flex-grow-width"
          />
          <div v-if="!translation.is_main && d.id !== 'title'" class="mt-4">
            <s-tooltip v-if="d.id in translation.data">
              <template #activator="{ on }">
                <s-btn @click="translateFieldReset(translation, d.id)" :disabled="readonly" icon small v-on="on">
                  <v-icon small>mdi-pencil-off</v-icon>
                </s-btn>
              </template>
              <span>
                Reset field to inherit text from the main language {{ mainLanguageInfo.name }}.
                Currently it is overridden for the {{ currentLanguageInfo.name }} translation.<br>
              </span>
            </s-tooltip>
            <s-tooltip v-else>
              <template #activator="{ on }">
                <s-btn @click="translateFieldCopy(translation, d.id)" :disabled="readonly" icon small v-on="on">
                  <v-icon small>mdi-pencil</v-icon>
                </s-btn>
              </template>
              <span>
                Override field in {{ currentLanguageInfo.name }} translation.<br>
                Currently it is inherited from the main language {{ mainLanguageInfo.name }}.
              </span>
            </s-tooltip>
          </div>
        </div>
      </v-tab-item>
    </v-tabs-items>
  </div>
</template>

<script>
import { cloneDeep } from 'lodash';
import { set } from 'vue';
import { v4 as uuidv4 } from 'uuid';

export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    initialLanguage: {
      type: String,
      default: null,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    toolbarAttrs: {
      type: Object,
      default: () => ({}),
    },
    toolbarEvents: {
      type: Object,
      default: () => ({}),
    },
    uploadFile: {
      type: Function,
      default: null,
    },
    rewriteFileUrl: {
      type: Function,
      default: null,
    },
  },
  emit: ['input'],
  data() {
    return {
      currentTranslation: this.value.translations.find(tr => tr.language === this.initialLanguage) || this.value.translations.find(tr => tr.is_main),
      restoreTranslationDataCache: {},
      initialLanguages: this.value.translations.map(tr => tr.language),
    };
  },
  async fetch() {
    await this.$store.dispatch('templates/getFieldDefinition');
  },
  computed: {
    template() {
      return this.value;
    },
    mainTranslation() {
      return this.template.translations.find(tr => tr.is_main);
    },
    templateTagSuggestions() {
      return [
        'web', 'infrastructure', 'organizational', 'hardening', 'internal', 'external', 'third_party',
        'active_directory', 'windows', 'client', 
        'config', 'update', 'development', 'crypto',
      ];
    },
    fieldDefinition() {
      return this.$store.getters['templates/fieldDefinitionList'];
    },
    visibleFieldDefinitions() {
      return this.fieldDefinition.filter(f => f.visible);
    },
    visibleFieldDefinitionsExceptTitle() {
      return this.visibleFieldDefinitions.filter(f => f.id !== 'title');
    },
    fieldDefinitionTitle() {
      return this.fieldDefinition.find(f => f.id === 'title');
    },
    currentTab: {
      get() {
        return this.template?.translations?.findIndex(tr => tr.id === this.currentTranslation?.id);
      },
      set(idx) {
        this.currentTranslation = this.template?.translations?.[idx] || this.mainTranslation;
      },
    },
    availableLanguageInfos() {
      return this.$store.getters['apisettings/settings'].languages.filter(l => l.enabled || this.initialLanguages.includes(l.code));
    },
    unusedLanguageInfos() {
      return this.availableLanguageInfos.filter(l => 
        !this.template.translations.some(tr => tr.language === l.code));
    },
    currentLanguageInfo() {
      return this.languageInfo(this.currentTranslation?.language);
    },
    mainLanguageInfo() {
      return this.languageInfo(this.mainTranslation?.language);
    },
  },
  watch: {
    template: {
      deep: true,
      handler() {
        this.currentTranslation = this.template?.translations?.find(tr => tr.id === this.currentTranslation?.id) ||
          this.template?.translations?.find(tr => tr?.language === this.currentTranslation?.language) ||
          this.mainTranslation;
      }
    },
  },
  methods: {
    updateTemplateField(fieldId, value) {
      const template = Object.assign({}, this.template, { [fieldId]: value });
      this.$emit('input', template);
    },
    updateTranslationField(translation, fieldId, value) {
      this.updateTemplateField('translations', this.template.translations.map(tr => 
        tr.id === translation.id ? Object.assign({}, tr, { [fieldId]: value }) : tr));
    },
    updateTranslationData(translation, fieldId, value) {
      const data = Object.fromEntries(Object.entries(translation.data).filter(([k, v]) => k !== fieldId));
      if (value !== undefined) {
        data[fieldId] = value;
      }
      this.updateTranslationField(translation, 'data', data);
    },
    languageInfo(languageCode) {
      return this.$store.getters['apisettings/settings'].languages.find(l => l.code === languageCode) || { code: '??-??', name: 'Unknown' };
    },
    translateFieldCopy(translation, fieldId) {
      // Restore previous value or copy field from main translation
      const restoreValue = this.restoreTranslationDataCache[translation.id]?.[fieldId] || cloneDeep(this.mainTranslation.data[fieldId]);
      this.updateTranslationData(translation, fieldId, restoreValue !== undefined ? restoreValue : null);
    },
    translateFieldReset(translation, fieldId) {
      // Store old content in cache to be able to restore value
      if (!this.restoreTranslationDataCache[translation.id]) {
        set(this.restoreTranslationDataCache, translation.id, {});
      }
      set(this.restoreTranslationDataCache[translation.id], fieldId, translation.data[fieldId]);
      // Remove field from translation (uses value from main translation)
      this.updateTranslationData(translation, fieldId, undefined);
    },
    async createTranslation(language) {
      this.updateTemplateField('translations', [...this.template.translations].concat({
        id: uuidv4(),
        language,
        status: 'in-progress',
        is_main: false,
        data: {
          title: this.mainTranslation.data.title,
        },
      }));
      await this.$nextTick();
      this.currentTranslation = this.template.translations.find(tr => tr.language === language);
    },
    deleteTranslation(translationId) {
      this.updateTemplateField('translations', this.template.translations.filter(tr => tr.id !== translationId))
    },
  },
}
</script>

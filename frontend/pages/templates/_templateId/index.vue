<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <template-field-selector />
    </template>

    <template #default>
      <fetch-loader v-bind="fetchLoaderAttrs">
        <template-editor 
          ref="templateEditor"
          v-if="template" 
          v-model="template" 
          :toolbar-attrs="toolbarAttrs" 
          :toolbar-events="toolbarEvents"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :readonly="readonly"
          :initial-language="template.translations.find(tr => tr.id === $route.query?.translation_id)?.language || $route.query?.language"
          :history="true"
        >
          <template #toolbar-context-menu v-if="$auth.hasScope('template_editor')">
            <btn-export 
              :export-url="`/findingtemplates/${template.id}/export/`" 
              :name="`template-` + mainTranslation.data.title" 
              list-item
            />
          </template>
        </template-editor>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script>
import urlJoin from "url-join"
import { set } from 'vue';
import { isEqual } from 'lodash';
import { uploadFileHelper } from '~/utils/upload';
import { EditMode } from '~/utils/other';
import LockEditMixin from '~/mixins/LockEditMixin';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
      editMode: (this.$auth.hasScope('template_editor')) ? EditMode.EDIT : EditMode.READONLY,
      template: null,
      currentTranslation: null,
      restoreTranslationDataCache: {},
      initialLanguages: [],
    };
  },
  async fetch() {
    const [template, _fieldDefinition] = await Promise.all([
      this.$axios.$get(this.getBaseUrl({ id: this.$route.params.templateId })),
      this.$store.dispatch('templates/getFieldDefinition'),
    ]);
    
    this.template = template;
  },
  head() {
    const title = this.mainTranslation?.data?.title;
    return {
      title: (title ? `${title} | ` : '') + 'Templates',
    };
  },
  computed: {
    data() {
      return this.template;
    },
    deleteConfirmInput() {
      return this.mainTranslation?.data?.title;
    },
    mainTranslation() {
      return this.template?.translations?.find(tr => tr.is_main);
    },
    menuSize: {
      get() {
        return this.$store.state.settings.templateInputMenuSize;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateInputMenuSize', val);
      }
    },
    toolbarAttrs() {
      return {
        ...LockEditMixin.computed.toolbarAttrs.call(this),
        canAutoSave: true,
      };
    },
  },
  methods: {
    getBaseUrl(data) {
      return `/findingtemplates/${data.id}/`
    },
    getHasEditPermissions() {
      return this.$auth.hasScope('template_editor');
    },
    getToolbarRef() {
      return this.$refs.templateEditor?.$refs?.toolbar;
    },
    updateTemplateField(translation, fieldId, value) {
      set(translation.data, fieldId, value);
    },
    async performSave(data) {
      const res = await this.$store.dispatch('templates/update', data);
      for (const tr of this.template.translations) {
        if (!res.translations.some(rtr => rtr.id === tr.id)) {
          // Set server-generated ID of newly created translations
          tr.id = res.translations.find(rtr => rtr.language === tr.language)?.id || tr.id;
        }
      }
    },
    async performDelete(data) {
      await this.$store.dispatch('templates/delete', data)
      this.$router.push(`/templates/`);
    },
    async onUpdateData({ oldValue, newValue }) {
      // Auto save when translation is added/deleted or language changed
      const toolbar = this.getToolbarRef();
      if (toolbar?.autoSaveEnabled && (
        oldValue.translations.length !== newValue.translations.length ||
        !isEqual(oldValue.translations.map(tr => tr.language), newValue.translations.map(tr => tr.language))
      )) {
        await toolbar.performSave();
      }
    },
    async uploadFile(file) {
      const img = await uploadFileHelper(this.$axios, urlJoin(this.baseUrl, '/images/'), file);
      return `![](/images/name/${img.name})`;
    },
    rewriteFileUrl(imgSrc) {
      return urlJoin(this.baseUrl, imgSrc);
    },
  },
}
</script>

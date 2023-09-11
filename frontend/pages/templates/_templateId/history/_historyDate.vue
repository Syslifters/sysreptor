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
          :rewrite-file-url="rewriteFileUrl"
          :readonly="true"
          :initial-language="template.translations.find(tr => tr.id === $route.query?.translation_id)?.language || $route.query?.language"
          :history="true"
        >
          <template #toolbar-actions>
            <s-btn color="secondary" :to="`/templates/${template.id}/`" nuxt exact class="ml-1 mr-1">
              <v-icon left>mdi-undo</v-icon>
              Back to current version
            </s-btn>
          </template>
        </template-editor>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script>
import urlJoin from "url-join"
import { formatISO9075 } from 'date-fns';
import LockEditMixin from '~/mixins/LockEditMixin';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
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
  },
  methods: {
    getBaseUrl(data) {
      return `/findingtemplates/${data.id}/history/${this.$route.params.historyDate}/`;
    },
    getHasEditPermissions() {
      return false;
    },
    getErrorMessage() {
      return `This is a historical version from ${formatISO9075(new Date(this.$route.params.historyDate))}.`;
    },
    getToolbarRef() {
      return this.$refs.templateEditor?.$refs?.toolbar;
    },
    rewriteFileUrl(imgSrc) {
      return urlJoin(this.baseUrl, imgSrc);
    },
  },
}
</script>

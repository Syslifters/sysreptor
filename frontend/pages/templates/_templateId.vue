<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list dense>
        <v-list-item>
          <project-type-selection
            v-model="fieldFilterDesign"
            label="Show fields of"
            :query-filters="{scope: ['global']}"
            :outlined="false"
            :additional-items="[{id: 'all', name: 'All Designs'}]"
          />
        </v-list-item>

        <v-list-item v-for="d in fieldDefinition" :key="d.id">
          <v-list-item-title>{{ d.id }}</v-list-item-title>
          <v-list-item-action v-if="d.origin !== 'core'">
            <s-btn @click="toggleFieldVisible(d)" icon x-small>
              <v-icon v-if="d.visible">mdi-eye</v-icon>
              <v-icon v-else>mdi-eye-off</v-icon>
            </s-btn>
          </v-list-item-action>
        </v-list-item>
      </v-list>
    </template>

    <template #default>
      <fetch-loader v-bind="fetchLoaderAttrs">
        <div v-if="template" :key="template?.id">
          <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
            <status-selection v-model="template.status" :disabled="readonly" />
            <template v-if="$auth.hasScope('template_editor')">
              <btn-export :export-url="`/findingtemplates/${template.id}/export/`" :name="`template-` + template.data.title" />
            </template>
          </edit-toolbar>

          <div v-for="d in fieldDefinitionsCore" :key="d.id">
            <dynamic-input-field 
              v-model="template.data[d.id]" 
              :id="d.id" 
              :definition="d" 
              :selectable-users="[]" 
              :lang="template.language"
              :disabled="readonly"
            />
          </div>
          <language-selection v-model="template.language" :disabled="readonly" />
          <s-tags v-model="template.tags" :items="templateTagSuggestions" />
          <div v-for="d in visibleFieldDefinitionsExceptCore" :key="d.id">
            <dynamic-input-field 
              v-model="template.data[d.id]" 
              :id="d.id" 
              :definition="d" 
              :selectable-users="[]" 
              :lang="template.language"
              :disabled="readonly"
            />
          </div>
        </div>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script>
import { sortBy } from 'lodash';
import { EditMode } from '~/utils/other';
import LockEditMixin from '~/mixins/LockEditMixin';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
      editMode: (this.$auth.hasScope('template_editor')) ? EditMode.EDIT : EditMode.READONLY,
      template: null,
      fieldDefinition: [],
    };
  },
  async fetch() {
    const [template, rawFieldDefinition] = await Promise.all([
      this.$axios.$get(this.getBaseUrl({ id: this.$route.params.templateId })),
      this.$store.dispatch('templates/getFieldDefinition'),
    ]);

    this.template = template;
    this.fieldDefinition = sortBy(
      Object.keys(rawFieldDefinition).map(id => ({ id, visible: !this.fieldFilterHiddenFields.includes(id), ...rawFieldDefinition[id] })),
      [(d) => {
        const originOrder = { core: 1, predefined: 2, custom: 3 };
        return originOrder[d.origin] || 10;
      }]);
  },
  head() {
    const title = this.template?.data?.title;
    return {
      title: (title ? `${title} | ` : '') + 'Templates',
    };
  },
  computed: {
    data() {
      return this.template;
    },
    deleteConfirmInput() {
      return this.template.data.title;
    },
    templateTagSuggestions() {
      return [
        'web', 'infrastructure', 'organizational', 'hardening', 'internal', 'external', 'third_party',
        'active_directory', 'windows', 'client', 
        'config', 'update', 'development', 'crypto',
      ];
    },
    visibleFieldDefinitions() {
      return this.fieldDefinition.filter(f => f.visible);
    },
    visibleFieldDefinitionsExceptCore() {
      return this.visibleFieldDefinitions.filter(f => f.origin !== 'core');
    },
    fieldDefinitionsCore() {
      return this.fieldDefinition.filter(f => f.origin === 'core');
    },
    fieldFilterDesign: {
      get() {
        return this.$store.state.settings.templateFieldFilterDesign;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateFieldFilterDesign', val);
      }
    },
    fieldFilterHiddenFields: {
      get() {
        return this.$store.state.settings.templateFieldFilterHiddenFields;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateFieldFilterHiddenFields', val);
      }
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
  watch: {
    async fieldFilterDesign(val) {
      if (val === 'all') {
        this.fieldFilterHiddenFields = [];
      } else {
        try {
          const projectType = await this.$store.dispatch('projecttypes/getById', val);
          this.fieldFilterHiddenFields = this.fieldDefinition.filter(d => !Object.keys(projectType.finding_fields).includes(d.id)).map(d => d.id);
        } catch (error) {
          this.fieldFilterDesign = 'all';
        }
      }
    },
    fieldFilterHiddenFields: {
      immediate: true,
      handler(val) {
        this.fieldDefinition.forEach((d) => {
          d.visible = !val.includes(d.id);
        });
      },
    }
  },
  methods: {
    getBaseUrl(data) {
      return `/findingtemplates/${data.id}/`
    },
    getHasEditPermissions() {
      return this.$auth.hasScope('template_editor');
    },
    async performSave(data) {
      await this.$store.dispatch('templates/update', data);
    },
    async performDelete(data) {
      await this.$store.dispatch('templates/delete', data)
      this.$router.push(`/templates/`);
    },
    toggleFieldVisible(d) {
      d.visible = !d.visible;
      this.fieldFilterHiddenFields = this.fieldDefinition.filter(d => !d.visible).map(d => d.id);
    }
  }
}
</script>

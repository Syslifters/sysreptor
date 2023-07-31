<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <template-field-selector />
    </template>

    <template #default>
      <fetch-loader :fetch-state="$fetchState">
        <template-editor 
          v-if="template"
          v-model="template" 
          :toolbar-attrs="toolbarAttrs" 
          :rewrite-file-url="rewriteFileUrl"
        />

        <s-dialog v-model="saveWarningDialogVisible">
          <template #title>Remove customer data</template>
          <template #default>
            <v-card-text>
              <v-alert type="warning">
                Ensure that no customer specific data is left in the template before saving.
              </v-alert>
              <p>
                Make sure that the following data is removed and replaced with <code>TODO</code> markers:
              </p>
              <ul>
                <li>Customer specific descriptions</li>
                <li>URLs, hostnames, system identifiers</li>
                <li>Screenshots</li>
              </ul>
            </v-card-text>

            <v-card-actions>
              <v-spacer />
              <s-btn @click="saveWarningDialogVisible = false" color="secondary">Cancel</s-btn>
              <btn-confirm 
                :action="() => performCreate()"
                :confirm="false"
                button-text="Save"
                button-icon="mdi-save"
                button-color="primary"
              />
            </v-card-actions>
          </template>
        </s-dialog>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script>
import { v4 as uuidv4 } from 'uuid';
import urlJoin from "url-join"

export default {
  data() {
    return {
      template: null,
      project: null,
      saveWarningDialogVisible: false,
    }
  },
  async fetch() {
    const projectId = this.$route.query.project;
    const findingId = this.$route.query.finding;
    if (!projectId && !findingId) {
      throw new Error('No project or finding found.')
    }

    const [project, finding, _fieldDefintion] = await Promise.all([
      this.$store.dispatch('projects/getById', projectId),
      this.$axios.$get(`/pentestprojects/${projectId}/findings/${findingId}/`),
      this.$store.dispatch('templates/getFieldDefinition'),
    ]);

    this.project = project;
    this.template = {
      id: uuidv4(),
      tags: [],
      translations: [{
        id: uuidv4(),
        is_main: true,
        language: finding.language,
        status: 'in-progress',
        data: Object.fromEntries(Object.entries(finding.data).filter(([key, value]) => {
          // Only copy fields that have an value and are also in the template field definition
          return value && value !== [] && this.$store.getters['templates/fieldDefinitionList'].some(d => d.id === key);
        })),
      }],
    };
    // Make all finding fields visible (keep visible template fields visible)
    this.$store.commit(
      'settings/updateTemplateFieldFilterHiddenFields', 
      this.$store.getters['settings/templateFieldFilterHiddenFields'].filter(f => !Object.keys(finding.data).includes(f)));
  },
  head: {
    title: 'Templates',
  },
  computed: {
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
        save: this.showSaveWarningDialog,
        saveButtonText: 'Create',
      };
    },
  },
  methods: {
    rewriteFileUrl(imgSrc) {
      return urlJoin(`/pentestprojects/${this.project.id}/`, imgSrc);
    },
    showSaveWarningDialog() {
      this.saveWarningDialogVisible = true;
    },
    async performCreate() {
      const obj = await this.$store.dispatch('templates/createFromFinding', { template: this.template, projectId: this.project.id });
      this.$router.push(`/templates/${obj.id}/`);
    }
  }
}
</script>

<template>
  <s-dialog v-model="dialogVisible">
    <template #activator="{ on, attrs }">
      <s-btn :disabled="project.readonly" color="secondary" small block v-bind="attrs" v-on="on">
        <v-icon>mdi-plus</v-icon>
        Create
      </s-btn>
    </template>
    <template #title>New Finding</template>

    <template #default>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="9">
            <s-combobox 
              v-model="currentTemplate"
              :search-input.sync="templates.searchQuery"
              label="Finding Templates"
              :items="templates.data"
              item-value="id"
              no-filter
              clearable
              return-object
              autofocus
              class="template-select"
            >
              <template #selection="{item}">
                <template-select-item v-if="item?.id" :value="item" :language="displayLanguage" />
                <template v-else>
                  {{ item }}
                </template>
              </template>
              <template #item="{item}">
                <template-select-item :value="item" :language="displayLanguage" />
              </template>

              <template #append-item>
                <page-loader :items="templates" />
              </template>
            </s-combobox>
          </v-col>
          <v-col cols="12" md="3">
            <language-selection 
              v-model="templateLanguage" 
              :items="templateLanguageChoices"
              :disabled="!currentTemplate"
            />
          </v-col>
        </v-row>
      </v-card-text>
        
      <v-card-actions>
        <v-spacer />
        <s-btn @click="closeDialog" color="secondary">
          Cancel
        </s-btn>
        <s-btn v-if="currentTemplate?.id" @click="createFindingFromTemplate" :loading="actionInProress" color="primary">
          Create from Template
        </s-btn>
        <s-btn v-else @click="createEmptyFinding" :loading="actionInProress" color="primary">
          Create Empty Finding
        </s-btn>
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script>
import { SearchableCursorPaginationFetcher } from '~/utils/urls';

export default {
  props: {
    project: {
      type: Object,
      required: true,
    }
  },
  data() {
    return {
      dialogVisible: false,
      currentTemplate: null,
      actionInProress: false,
      templates: new SearchableCursorPaginationFetcher({
        baseURL: '/findingtemplates/', 
        searchFilters: { ordering: '-usage', preferred_language: this.project.language },
        axios: this.$axios, 
        toast: this.$toast
      }),
      templateLanguage: null,
    }
  },
  computed: {
    templateLanguageChoices() {
      return this.currentTemplate?.translations?.map(tr => this.$store.getters['apisettings/settings'].languages.find(l => l.code === tr.language)) || [];
    },
    displayLanguage() {
      return this.templateLanguage || this.project.language;
    },
  },
  watch: {
    dialogVisible() {
      this.currentTemplate = null;
      this.templates.searchQuery = null;
    },
    currentTemplate() {
      if (!this.currentTemplate) {
        this.templateLanguage = null;
      } else if (this.currentTemplate.translations.some(tr => tr.language === this.templateLanguage)) {
        // Keep current templateLanguage
      } else if (this.currentTemplate.translations.some(tr => tr.language === this.project.language)) {
        this.templateLanguage = this.project.language;
      } else {
        this.templateLanguage = this.currentTemplate.translations.find(tr => tr.is_main).language;
      }
    },
  },
  methods: {
    filterTemplate(template, queryText) {
      const toTokens = s => s.toLocaleLowerCase().split(' ').filter(t => Boolean(t));

      const templateTokens = toTokens(template.data.title).concat(...template.tags.map(toTokens));
      return toTokens(queryText).every(qt => templateTokens.some(tt => tt.includes(qt)));
    },
    closeDialog() {
      this.dialogVisible = false;
    },
    async createEmptyFinding() {
      try {
        this.actionInProress = true;
        const title = this.currentTemplate || this.templates.searchQuery;
        const finding = await this.$store.dispatch('projects/createFinding', {
          projectId: this.project.id, 
          finding: { 
            data: {
              ...(title ? { title } : {}) 
            }
          },
        });
        this.$router.push({ path: `/projects/${finding.project}/reporting/findings/${finding.id}/` });
        this.closeDialog();
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProress = false;
      }
    },
    async createFindingFromTemplate() {
      try {
        this.actionInProress = true;
        const finding = await this.$store.dispatch('projects/createFindingFromTemplate', { 
          projectId: this.project.id, 
          templateId: this.currentTemplate.id,
          templateLanguage: this.templateLanguage,
        });
        this.$router.push({ path: `/projects/${finding.project}/reporting/findings/${finding.id}/` });
        this.closeDialog();
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProress = false;
      }
    },
  }
}
</script>

<style lang="scss" scoped>
.template-select {
  :deep(.v-select__selections) > input {
    min-width: 0 !important;
  }
}
</style>

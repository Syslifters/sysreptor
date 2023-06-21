<template>
  <s-dialog v-model="dialogVisible">
    <template #activator="{ on, attrs }">
      <s-btn :disabled="project.readonly" color="secondary" small v-bind="attrs" v-on="on">
        <v-icon>mdi-plus</v-icon>
        Create
      </s-btn>
    </template>
    <template #title>New Finding</template>

    <template #default>
      <v-card-text>
        <s-combobox 
          v-model="currentSelection"
          :search-input.sync="templates.searchQuery"
          label="Finding Templates"
          :items="templates.data"
          item-value="id"
          no-filter
          clearable
          return-object
          autofocus
        >
          <template #selection="{item}">
            <template v-if="item?.id">
              <chip-cvss :value="item.data.cvss" />
              {{ item.data.title }}
            </template>
            <template v-else>
              {{ item }}
            </template>
          </template>
          <template #item="{item}">
            <v-list-item-title class="d-flex">
              <chip-cvss :value="item.data.cvss" /> 
              <div class="pt-2 pb-2">
                {{ item.data.title }}
                <br />
                <chip-review-status v-if="item.status !== 'finished'" :value="item.status" />
                <chip-language v-if="!showOnlyMatchingLanguage" :value="item.language" />
                <chip-tag v-for="tag in item.tags" :key="tag" :value="tag" />
              </div>
              <v-spacer />
              <s-btn :to="`/templates/${item.id}/`" target="_blank" nuxt icon class="ma-2">
                <v-icon>mdi-chevron-right-circle</v-icon>
              </s-btn>
            </v-list-item-title>
          </template>

          <template #append-item>
            <page-loader :items="templates" />
          </template>
        </s-combobox>
        <s-checkbox 
          v-model="showOnlyMatchingLanguage"
          label="Show only templates with matching language" 
          dense
        />
      </v-card-text>
        
      <v-card-actions>
        <v-spacer />
        <s-btn @click="closeDialog" color="secondary">
          Cancel
        </s-btn>
        <s-btn v-if="currentSelection?.id" @click="createFindingFromTemplate" :loading="actionInProress" color="primary">
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
      currentSelection: null,
      actionInProress: false,
      templates: new SearchableCursorPaginationFetcher({
        baseURL: '/findingtemplates/', 
        searchFilters: { ordering: '-usage', language: this.project.language },
        axios: this.$axios, 
        toast: this.$toast
      }),
    }
  },
  computed: {
    showOnlyMatchingLanguage: {
      get() {
        return this.templates.searchFilters.language === this.project.language;
      },
      set(val) {
        this.templates.applyFilters({ language: val ? this.project.language : null });
      }
    }
  },
  watch: {
    dialogVisible() {
      this.currentSelection = null;
      this.templates.searchQuery = null;
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
        const title = this.currentSelection || this.templates.searchQuery;
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
        const finding = await this.$store.dispatch('projects/createFindingFromTemplate', { projectId: this.project.id, templateId: this.currentSelection.id });
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

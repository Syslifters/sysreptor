<template>
  <v-dialog v-model="dialogVisible" max-width="50%">
    <template #activator="{ on, attrs }">
      <s-btn color="secondary" small v-bind="attrs" v-on="on">
        <v-icon>mdi-plus</v-icon>
        Create Finding
      </s-btn>
    </template>

    <template #default>
      <s-card>
        <v-card-title>
          <v-toolbar flat>
            <v-toolbar-title>Create Finding</v-toolbar-title>
            <v-spacer />
            <s-tooltip>
              <template #activator="{attrs, on}">
                <s-btn v-bind="attrs" v-on="on" @click="closeDialog" icon x-large>
                  <v-icon>mdi-close-thick</v-icon>
                </s-btn>
              </template>
              <span>Cancel</span>
            </s-tooltip>
          </v-toolbar>
        </v-card-title>

        <v-card-text>
          <s-autocomplete 
            v-model="currentTemplate"
            label="Finding Templates"
            :items="templates.data"
            item-value="id" item-text="data.title"
            :search-input.sync="templates.searchQuery"
            no-filter
            clearable
            return-object
          >
            <template #selection="{item}">
              <cvss-chip :value="item.data.cvss" />
              {{ item.data.title }}
            </template>
            <template #item="{item}">
              <v-list-item-title class="d-flex">
                <cvss-chip :value="item.data.cvss" /> 
                <div class="pt-2 pb-2">
                  {{ item.data.title }}
                  <br />
                  <language-chip :value="item.language" />
                  <v-chip v-for="tag in item.tags" :key="tag" class="ma-1" small>
                    {{ tag }}
                  </v-chip>
                </div>
              </v-list-item-title>
            </template>

            <template #append-item>
              <div v-if="templates.hasNextPage" v-intersect="templates.fetchNextPage()" />
            </template>
          </s-autocomplete>
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
          <s-btn v-if="currentTemplate" @click="createFindingFromTemplate" color="primary">
            Create from Template
          </s-btn>
          <s-btn v-else @click="createEmptyFinding" color="primary">
            Create Empty Finding
          </s-btn>
        </v-card-actions>
      </s-card>
    </template>
  </v-dialog>
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
      templates: new SearchableCursorPaginationFetcher({
        baseURL: '/findingtemplates/', 
        searchFilters: { language: this.project.language },
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
  methods: {
    filterTemplate(template, queryText) {
      const toTokens = s => s.toLocaleLowerCase().split(' ').filter(t => Boolean(t));

      const templateTokens = toTokens(template.data.title).concat(...template.tags.map(toTokens));
      return toTokens(queryText).every(qt => templateTokens.some(tt => tt.includes(qt)));
    },
    closeDialog() {
      this.dialogVisible = false;
      this.currentTemplate = null;
    },
    async createEmptyFinding() {
      try {
        const finding = await this.$store.dispatch('projects/createFinding', this.project.id);
        this.$router.push({ path: `/projects/${finding.project}/reporting/findings/${finding.id}/` });
        this.closeDialog();
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
    async createFindingFromTemplate() {
      try {
        const finding = await this.$store.dispatch('projects/createFindingFromTemplate', { projectId: this.project.id, templateId: this.currentTemplate.id });
        this.$router.push({ path: `/projects/${finding.project}/reporting/findings/${finding.id}/` });
        this.closeDialog();
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
  }
}
</script>

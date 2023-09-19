<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="finding && project && projectType" :key="project?.id + finding?.id">
      <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents">
        <status-selection v-model="finding.status" :disabled="readonly" />
        <div class="assignee-container ml-1 mr-1">
          <user-selection 
            v-model="finding.assignee" 
            :selectable-users="project.members" 
            :disabled="readonly" 
            label="Assignee"
            :outlined="false" dense
          />
        </div>

        <s-btn 
          v-if="currentUrl"
          :to="currentUrl" nuxt exact 
          color="secondary" class="ml-1 mr-1"
        >
          <v-icon left>mdi-undo</v-icon>
          Back to current version
        </s-btn>

        <s-btn @click="historyVisible = !historyVisible" color="secondary">
          <v-icon left>mdi-history</v-icon>
          Version History
        </s-btn>
      </edit-toolbar>

      <project-history-timeline 
        v-model="historyVisible"
        :project="project"
        :finding="finding"
        :current-url="currentUrl"
      />

      <div v-for="fieldId in projectType.finding_field_order" :key="fieldId">
        <dynamic-input-field 
          v-model="finding.data[fieldId]" 
          :disabled="readonly"
          :id="fieldId" 
          :definition="projectType.finding_fields[fieldId]" 
          :upload-file="uploadFile" 
          :rewrite-file-url="rewriteFileUrl"
          :rewrite-reference-link="rewriteReferenceLink"
          :selectable-users="project.members.concat(project.imported_members)"
          :lang="finding.language"
        />
      </div>
    </div>
  </fetch-loader>
</template>

<script>
import urlJoin from 'url-join';
import ProjectHistoryMixin from '~/mixins/ProjectHistoryMixin';

export default {
  mixins: [ProjectHistoryMixin],
  data() {
    return {
      finding: null,
      project: null,
      projectType: null,
      historyVisible: false,
    }
  },
  async fetch() {
    const [finding, project] = await Promise.all([
      this.$axios.$get(this.getBaseUrl({ id: this.$route.params.findingId })),
      this.$axios.$get(this.projectUrl)
    ]);
    this.project = project;
    this.projectType = await this.$axios.$get(this.projectTypeUrl);
    this.finding = finding;
  },
  computed: {
    data() {
      return this.finding;
    },
    currentUrl() {
      if (this.$store.getters['projects/findings'](this.project.id).map(f => f.id).includes(this.finding.id)) {
        return `/projects/${this.$route.params.projectId}/reporting/findings/${this.$route.params.findingId}/`;
      }
      return null;
    }
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `findings/${data.id}/`);
    },
  }
};
</script>

<style lang="scss" scoped>
.assignee-container {
  width: 17em;
}
</style>

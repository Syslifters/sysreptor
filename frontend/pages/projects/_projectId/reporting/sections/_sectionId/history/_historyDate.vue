<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="section && project && projectType" :key="project.id + section.id">
      <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
        <status-selection v-model="section.status" :disabled="readonly" />
        <div class="assignee-container ml-1 mr-1">
          <user-selection 
            v-model="section.assignee" 
            :selectable-users="project.members" 
            :disabled="readonly" 
            label="Assignee"
            :outlined="false" dense
          />
        </div>

        <s-btn :to="`/projects/${$route.params.projectId}/reporting/sections/${$route.params.sectionId}/`" nuxt exact color="secondary" class="ml-1 mr-1">
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
        :section="section"
      />

      <div v-for="fieldId in section.fields" :key="fieldId">
        <dynamic-input-field 
          v-model="section.data[fieldId]" 
          :disabled="readonly"
          :id="fieldId" 
          :definition="projectType.report_fields[fieldId]" 
          :upload-file="uploadFile" 
          :rewrite-file-url="rewriteFileUrl"
          :rewrite-reference-link="rewriteReferenceLink"
          :selectable-users="project.members.concat(project.imported_members)"
          :lang="section.language"
        />
      </div>
    </div>
  </fetch-loader>
</template>

<script>
import urlJoin from 'url-join';
import ProjectLockEditMixin from '~/mixins/ProjectLockEditMixin';

export default {
  mixins: [ProjectLockEditMixin],
  data() {
    return {
      section: null,
      project: null,
      projectType: null,
      historyVisible: false,
    }
  },
  async fetch() {
    const [section, project] = await Promise.all([
      this.$axios.$get(this.getBaseUrl({ id: this.$route.params.sectionId })),
      this.$axios.$get(this.projectUrl),
    ]);
    this.project = project;
    this.projectType = await this.$axios.$get(this.projectTypeUrl);
    this.section = section;
  },
  computed: {
    data() {
      return this.section;
    },
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `/sections/${data.id}/`)
    },
  }
}
</script>

<style lang="scss" scoped>
.assignee-container {
  width: 17em;
}
</style>

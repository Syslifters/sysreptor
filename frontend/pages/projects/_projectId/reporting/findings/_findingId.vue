<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="finding && project && projectType" :key="project?.id + finding?.id">
      <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
        <s-tooltip v-if="finding.template">
          <template #activator="{attrs, on}">
            <s-btn icon :to="`/templates/${finding.template}/`" nuxt target="_blank" class="ml-1 mr-1" v-bind="attrs" v-on="on">
              <v-icon>mdi-alpha-t-box-outline</v-icon>
            </s-btn>
          </template>
          <template #default>
            This finding was created from a template: show template
          </template>
        </s-tooltip>

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
      </edit-toolbar>

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
import ProjectLockEditMixin from '~/mixins/ProjectLockEditMixin.js';

export default {
  mixins: [ProjectLockEditMixin],
  data() {
    return {
      finding: null,
      project: null,
      projectType: null,
    }
  },
  async fetch() {
    const finding = await this.$axios.$get(this.getBaseUrl({ id: this.$route.params.findingId }));
    const [project, projectType] = await Promise.all([
      this.$store.dispatch('projects/getById', finding.project),
      this.$store.dispatch('projecttypes/getById', finding.project_type)
    ])
    this.project = project;
    this.projectType = projectType;
    this.finding = finding;
  },
  computed: {
    data() {
      return this.finding;
    },
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `findings/${data.id}/`);
    },
    async performSave(data) {
      await this.$store.dispatch('projects/updateFinding', { projectId: this.finding.project, finding: data });
    },
    async performDelete(data) {
      await this.$store.dispatch('projects/deleteFinding', { projectId: this.finding.project, findingId: data.id })
      this.$router.push(`/projects/${data.project}/reporting/`);
    },
    updateInStore(data) {
      this.$store.commit('projects/setFinding', { projectId: data.project, finding: data });
    },
    async onUpdateData({ oldValue, newValue }) {
      if (this.$refs.toolbar?.autoSaveEnabled && (
        oldValue.status !== newValue.status || 
        oldValue.assignee?.id !== newValue.assignee?.id || 
        oldValue.data.cvss !== newValue.data.cvss
      )) {
        await this.$refs.toolbar.performSave();
      }
    },
  }
};
</script>

<style lang="scss" scoped>
.assignee-container {
  width: 17em;
}

</style>

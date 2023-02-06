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
          :upload-image="uploadImage" 
          :rewrite-image-url="rewriteImageUrl"
          :selectable-users="project.members.concat(project.imported_members)"
          :lang="finding.language"
        />
      </div>
    </div>
  </fetch-loader>
</template>

<script>
import urlJoin from 'url-join';
import LockEditMixin from '~/mixins/LockEditMixin.js';
import { uploadFile } from '~/utils/upload.js';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
      finding: null,
      project: null,
      projectType: null,
    }
  },
  async fetch() {
    this.finding = await this.$axios.$get(this.getBaseUrl({ id: this.$route.params.findingId }));
    const [project, projectType] = await Promise.all([
      this.$store.dispatch('projects/getById', this.finding.project),
      this.$store.dispatch('projecttypes/getById', this.finding.project_type)
    ])
    this.project = project;
    this.projectType = projectType;
  },
  computed: {
    data() {
      return this.finding;
    },
    projectUrl() {
      return `/pentestprojects/${this.$route.params.projectId}/`;
    }
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `findings/${data.id}/`);
    },
    getHasEditPermissions() {
      if (this.project) {
        return !this.project.readonly;
      }
      return true;
    },
    getErrorMessage() {
      if (this.project?.readonly) {
        return 'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.'
      }
      return LockEditMixin.methods.getErrorMessage();
    },
    async performSave(data) {
      await this.$store.dispatch('projects/updateFinding', { projectId: this.finding.project, finding: data });
    },
    async performDelete(data) {
      await this.$store.dispatch('projects/deleteFinding', { projectId: this.finding.project, findingId: data.id })
      this.$router.push(`/projects/${data.project}/reporting/`);
    },
    async uploadImage(file) {
      const img = await uploadFile(this.$axios, urlJoin(this.projectUrl, '/images/'), file);
      return `/images/name/${img.name}`;
    },
    rewriteImageUrl(imgSrc) {
      if (imgSrc.startsWith('/assets/')) {
        return urlJoin(`/projecttypes/${this.projectType.id}/`, imgSrc);
      }
      return urlJoin(this.projectUrl, imgSrc);
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

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
      </edit-toolbar>

      <div v-for="fieldId in section.fields" :key="fieldId">
        <dynamic-input-field 
          v-model="section.data[fieldId]" 
          :disabled="readonly"
          :id="fieldId" 
          :definition="projectType.report_fields[fieldId]" 
          :upload-image="uploadImage" 
          :rewrite-image-url="rewriteImageUrl"
          :selectable-users="project.members.concat(project.imported_members)"
          :lang="section.language"
        />
      </div>
    </div>
  </fetch-loader>
</template>

<script>
import urlJoin from 'url-join';
import LockEditMixin from '~/mixins/LockEditMixin';
import { uploadFile } from '~/utils/upload';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
      section: null,
      project: null,
      projectType: null,
    }
  },
  async fetch() {
    const section = await this.$axios.$get(this.getBaseUrl({ id: this.$route.params.sectionId }));
    const [project, projectType] = await Promise.all([
      await this.$store.dispatch('projects/getById', section.project),
      await this.$store.dispatch('projecttypes/getById', section.project_type)
    ]);
    this.section = section;
    this.project = project;
    this.projectType = projectType;
  },
  computed: {
    data() {
      return this.section;
    },
    projectUrl() {
      return `/pentestprojects/${this.$route.params.projectId}/`;
    },
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `/sections/${data.id}/`)
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
      await this.$store.dispatch('projects/updateSection', { projectId: this.$route.params.projectId, section: data });
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
      this.$store.commit('projects/setSection', { projectId: this.section.project, section: data });
    },
    async onUpdateData({ oldValue, newValue }) {
      if (this.$refs.toolbar?.autoSaveEnabled && (oldValue.status !== newValue.status || oldValue.assignee?.id !== newValue.assignee?.id)) {
        await this.$refs.toolbar.performSave();
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.assignee-container {
  width: 17em;
}
</style>

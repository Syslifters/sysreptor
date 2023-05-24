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
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `/sections/${data.id}/`)
    },
    async performSave(data) {
      await this.$store.dispatch('projects/updateSection', { projectId: this.$route.params.projectId, section: data });
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

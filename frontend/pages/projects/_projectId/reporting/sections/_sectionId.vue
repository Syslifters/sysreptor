<template>
  <div>
    <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
      <status-selection v-model="section.status" :disabled="readonly" />
      <div class="assignee-container ml-1 mr-1">
        <user-selection 
          v-model="section.assignee" 
          :selectable-users="project.pentesters" 
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
        :selectable-users="project.pentesters.concat(project.imported_pentesters)"
        :lang="section.language"
      />
    </div>
  </div>
</template>

<script>
import urlJoin from 'url-join';
import DynamicInputField from '~/components/DynamicInputField.vue';
import LockEditMixin from '~/mixins/LockEditMixin';
import { uploadFile } from '~/utils/upload';

function getProjectUrl(params) {
  return `/pentestprojects/${params.projectId}/`;
}
function getSectionUrl(params) {
  return urlJoin(getProjectUrl(params), `/sections/${params.sectionId}/`);
}

export default {
  components: { DynamicInputField },
  mixins: [LockEditMixin],
  async asyncData({ $axios, store, params }) {
    const section = await $axios.$get(getSectionUrl(params));
    const project = await store.dispatch('projects/getById', section.project);
    const projectType = await store.dispatch('projecttypes/getById', section.project_type);
    return { section, project, projectType };
  },
  computed: {
    data() {
      return this.section;
    },
    projectUrl() {
      return getProjectUrl(this.$route.params);
    },
  },
  methods: {
    getBaseUrl(data) {
      return getSectionUrl({ projectId: data.project, sectionId: data.id });
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
  }
}
</script>

<style lang="scss" scoped>
.assignee-container {
  width: 17em;
}
</style>

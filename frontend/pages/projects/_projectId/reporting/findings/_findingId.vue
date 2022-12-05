<template>
  <div>
    <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
      <status-selection v-model="finding.status" :disabled="readonly" />
      <div class="assignee-container ml-1 mr-1">
        <user-selection 
          v-model="finding.assignee" 
          :selectable-users="project.pentesters" 
          :disabled="readonly" 
          label="Assignee"
          :outlined="false" dense
        />
      </div>
    </edit-toolbar>

    <p v-if="finding.template" class="text-right mt-1">
      This finding was created from a template:
      <nuxt-link :to="`/templates/${finding.template}/`" target="_blank">show template</nuxt-link>
    </p>

    <div v-for="fieldId in projectType.finding_field_order" :key="fieldId">
      <dynamic-input-field 
        v-model="finding.data[fieldId]" 
        :disabled="readonly"
        :id="fieldId" 
        :definition="projectType.finding_fields[fieldId]" 
        :upload-image="uploadImage" 
        :rewrite-image-url="rewriteImageUrl"
        :selectable-users="project.pentesters.concat(project.imported_pentesters)"
        :lang="finding.language"
      />
    </div>
  </div>
</template>

<script>
import urlJoin from 'url-join';
import DynamicInputField from '~/components/DynamicInputField.vue';
import LockEditMixin from '~/mixins/LockEditMixin.js';
import { uploadFile } from '~/utils/upload.js';
import UserSelection from '~/components/UserSelection.vue';

function getProjectUrl(params) {
  return `/pentestprojects/${params.projectId}/`;
}
function getFindingUrl(params) {
  return urlJoin(getProjectUrl(params), `/findings/${params.findingId}/`);
}

export default {
  components: { DynamicInputField, UserSelection },
  mixins: [LockEditMixin],
  async asyncData({ $axios, store, params }) {
    const finding = await $axios.$get(getFindingUrl(params));
    const project = await store.dispatch('projects/getById', finding.project);
    const projectType = await store.dispatch('projecttypes/getById', finding.project_type);
    return { finding, project, projectType };
  },
  computed: {
    data() {
      return this.finding;
    },
    projectUrl() {
      return getProjectUrl(this.$route.params);
    },
  },
  methods: {
    getBaseUrl(data) {
      return getFindingUrl(this.$route.params);
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
      this.$store.commit('projects/setFinding', { projectId: this.finding.project, finding: data });
    },
    async onUpdateData({ oldValue, newValue }) {
      if (this.$refs.toolbar?.autoSaveEnabled && (oldValue.status !== newValue.status || oldValue.assignee?.id !== newValue.assignee?.id)) {
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

<template>
  <div>
    <edit-toolbar v-bind="toolbarAttrs" />

    <v-alert v-if="errorMessageLocked" type="warning">
      {{ errorMessageLocked }}
    </v-alert>

    <div v-for="fieldId in projectType.finding_field_order" :key="fieldId">
      <dynamic-input-field 
        v-model="finding.data[fieldId]" :disabled="editMode === 'READONLY'"
        :id="fieldId" 
        :definition="projectType.finding_fields[fieldId]" 
        :upload-image="uploadImage" :image-urls-relative-to="projectUrl" 
        :selectable-users="project.pentesters"
      />
    </div>
  </div>
</template>

<script>
import urlJoin from 'url-join';
import DynamicInputField from '~/components/DynamicInputField.vue';
import LockEditMixin from '~/mixins/LockEditMixin.js';
import { uploadFile } from '~/utils/upload.js';

function getProjectUrl(params) {
  return `/pentestprojects/${params.projectId}/`;
}
function getFindingUrl(params) {
  return urlJoin(getProjectUrl(params), `/findings/${params.findingId}/`);
}

export default {
  components: { DynamicInputField },
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
    updateInStore(data) {
      this.$store.commit('projects/setFinding', { projectId: this.finding.project, finding: data });
    },
  }
};
</script>

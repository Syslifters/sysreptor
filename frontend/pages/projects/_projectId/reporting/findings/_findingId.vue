<template>
  <div>
    <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
      <div class="assignee-container">
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
      <nuxt-link :to="`/templates/${finding.template}/`">show template</nuxt-link>
    </p>

    <div v-for="fieldId in projectType.finding_field_order" :key="fieldId">
      <dynamic-input-field 
        v-model="finding.data[fieldId]" 
        :disabled="readonly"
        :id="fieldId" 
        :definition="projectType.finding_fields[fieldId]" 
        :upload-image="uploadImage" :image-urls-relative-to="projectUrl" 
        :selectable-users="project.pentesters"
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

<style lang="scss" scoped>
.assignee-container {
  width: 17em;
}
</style>

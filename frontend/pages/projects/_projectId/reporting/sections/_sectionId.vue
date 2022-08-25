<template>
  <div>
    <edit-toolbar v-bind="toolbarAttrs" />

    <v-alert v-if="errorMessageLocked" type="warning">
      {{ errorMessageLocked }}
    </v-alert>

    <div v-for="fieldId in section.fields" :key="fieldId">
      <dynamic-input-field 
        v-model="section.data[fieldId]" :disabled="editMode === 'READONLY'"
        :id="fieldId" 
        :definition="projectType.report_fields[fieldId]" 
        :upload-image="uploadImage" :image-urls-relative-to="`/pentestprojects/${$route.params.projectId}/`" 
        :selectable-users="project.pentesters"
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
    async performSave(data) {
      await this.$store.dispatch('projects/updateSection', { projectId: this.$route.params.projectId, section: data });
    },
    async uploadImage(file) {
      const img = await uploadFile(this.$axios, urlJoin(this.projectUrl, '/images/'), file);
      return `/images/name/${img.name}`;
    },
    updateInStore(data) {
      console.log('Section.updateInStore', data.id, data.lock_info);
      this.$store.commit('projects/setSection', { projectId: this.section.project, section: data });
    },
  }
}
</script>

<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/projects/${$route.params.projectId}/project/`">Project</v-tab>
      <v-tab :to="`/projects/${$route.params.projectId}/reporting/`">Reporting</v-tab>
      <v-tab :to="`/projects/${$route.params.projectId}/publish/`">Publish</v-tab>
      <v-tab :to="`/projects/${$route.params.projectId}/designer/`" v-if="projectType.source === 'customized'">Designer</v-tab>
    </s-sub-menu>

    <nuxt-child />
  </div>
</template>

<script>
export default {
  async asyncData({ store, params }) {
    const project = await store.dispatch('projects/getById', params.projectId);
    const projectType = await store.dispatch('projecttypes/getById', project.project_type);
    return { projectType };
  },
  computed: {
    project() {
      return this.$store.getters['projects/project'](this.$route.params.projectId);
    }
  },
  watch: {
    async 'project.project_type'() {
      this.projectType = await this.$store.dispatch('projecttypes/getById', this.project.project_type);
    }
  },
}
</script>

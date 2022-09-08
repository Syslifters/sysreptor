<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar ref="toolbar" :data="project" :form="$refs.form" :save="performSave" :delete="performDelete">
        <template #title>Project</template>
        <copy-button :copy="performCopy">
          <template #tooltip>Duplicate Project</template>
          <template #confirm-text>
            The whole project will be copied including all pentesters, sections, findings and images.
          </template>
        </copy-button>
      </edit-toolbar>

      <s-text-field v-model="project.name" label="Name" :error-messages="serverErrors?.name" class="mt-4" />
      <project-type-selection v-model="project.project_type" :error-messages="serverErrors?.project_type" />
      <language-selection v-model="project.language" :error-messages="serverErrors?.language" />
      <user-selection 
        v-model="project.pentesters" 
        :prevent-unselecting-self="true" 
        :required="true"
        :multiple="true" 
        :error-messages="serverErrors?.pentesters"
        class="mt-4"
      />
    </v-form>
  </v-container>
</template>

<script>
export default {
  beforeRouteLeave(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  beforeRouteUpdate(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  async asyncData({ params, $axios }) {
    return {
      project: await $axios.$get(`pentestprojects/${params.projectId}/`),
    };
  },
  data() {
    return {
      serverErrors: null,
    }
  },
  methods: {
    async performSave() {
      try {
        await this.$store.dispatch('projects/update', this.project);
        this.serverErrors = null;
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data) {
          this.serverErrors = error.response.data;
        }
        throw error;
      }
    },
    async performCopy() {
      const obj = await this.$axios.$post(`/pentestprojects/${this.project.id}/copy/`, {});
      this.$router.push({ path: `/projects/${obj.id}/project/` });
    },
    async performDelete() {
      await this.$store.dispatch('projects/delete', this.project);
      this.$router.push({ path: '/projects/' });
    }
  }
}
</script>

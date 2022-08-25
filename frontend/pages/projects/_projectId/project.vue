<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar ref="toolbar" :data="project" :form="$refs.form" :save="performSave" :delete="performDelete">
        <template #title>Project</template>
      </edit-toolbar>

      <s-text-field v-model="project.name" label="Name" />
      <project-type-selection v-model="project.project_type" />
      <user-selection v-model="project.pentesters" :prevent-unselecting-self="true" :required="true" :multiple="true" />
    </v-form>
  </v-container>
</template>

<script>
import ProjectTypeSelection from '~/components/ProjectTypeSelection.vue';
import UserSelection from '~/components/UserSelection.vue';
export default {
  components: { ProjectTypeSelection, UserSelection },
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
  methods: {
    async performSave() {
      await this.$store.dispatch('projects/update', this.project);
    },
    async performDelete() {
      await this.$store.dispatch('projects/delete', this.project);
      this.$router.push({ path: '/projects/' });
    }
  }
}
</script>

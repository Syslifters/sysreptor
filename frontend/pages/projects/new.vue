<template>
  <v-container>
    <v-form ref="form" @submit.prevent="performCreate">
      <edit-toolbar :form="$refs.form" :save="performCreate">
        <template #title>Create new Project</template>
        <template #save-button-text>Create</template>
      </edit-toolbar>

      <s-text-field v-model="project.name" label="Name" />
      <project-type-selection v-model="project.project_type" />
      <user-selection v-model="project.pentesters" :prevent-unselecting-self="true" :required="true" :multiple="true" class="mt-4" />
    </v-form>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      project: {
        name: 'New project',
        project_type: null,
        pentesters: [
          this.$store.state.auth.user,
        ],
      }
    }
  },
  methods: {
    async performCreate() {
      if (!this.$refs.form.validate()) {
        return;
      }

      try {
        const project = await this.$store.dispatch('projects/create', this.project);
        this.$router.push({ path: `/projects/${project.id}/reporting/` });
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    }
  }
}
</script>

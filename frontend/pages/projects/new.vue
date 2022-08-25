<template>
  <v-container>
    <v-form ref="form" @submit.prevent="performCreate">
      <v-toolbar flat dense tile>
        <v-toolbar-title>Create new project</v-toolbar-title>
        <v-spacer />
        <s-btn type="submit" color="primary">
          <v-icon>mdi-content-save</v-icon>
          Save
        </s-btn>
      </v-toolbar>

      <s-text-field v-model="project.name" label="Name" />
      <project-type-selection v-model="project.project_type" />
      <user-selection v-model="project.pentesters" :prevent-unselecting-self="true" :required="true" :multiple="true" />
    </v-form>
  </v-container>
</template>

<script>
import ProjectTypeSelection from '~/components/ProjectTypeSelection.vue'
import UserSelection from '~/components/UserSelection.vue'
export default {
  components: { ProjectTypeSelection, UserSelection },
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

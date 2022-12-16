<template>
  <v-container>
    <v-form ref="form" @submit.prevent="performCreate">
      <edit-toolbar :form="$refs.form" :save="performCreate">
        <template #title>Create new Project</template>
        <template #save-button-text>Create</template>
      </edit-toolbar>

      <s-text-field v-model="project.name" label="Name" />
      <project-type-selection v-model="project.project_type" />
      <member-selection v-model="project.members" :prevent-unselecting-self="true" :required="true" />
    </v-form>
  </v-container>
</template>

<script>
export default {
  async asyncData({ store, $auth }) {
    const settings = await store.dispatch('apisettings/getSettings');

    return {
      project: {
        name: 'New project',
        project_type: null,
        members: [
          { ...$auth.user, roles: settings.project_member_roles.filter(r => r.default).map(r => r.role) },
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

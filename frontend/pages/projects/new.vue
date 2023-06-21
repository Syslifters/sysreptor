<template>
  <v-container>
    <v-form ref="form" @submit.prevent="performCreate">
      <edit-toolbar :form="$refs.form" :save="performCreate">
        <template #title>Create new Project</template>
        <template #save-button-text>Create</template>
      </edit-toolbar>

      <s-text-field v-model="project.name" label="Name" class="mt-4" />
      <project-type-selection v-model="project.project_type" />
      <member-selection v-model="project.members" :prevent-unselecting-self="true" :required="true" />
      <s-tags v-model="project.tags" />
    </v-form>
  </v-container>
</template>

<script>
export default {
  data() {
    const roles = this.$store.getters['apisettings/settings'] 
      .project_member_roles
      .filter(r => r.default)
      .map(r => r.role)

    return {
      project: {
        name: '',
        project_type: null,
        tags: [],
        members: [
          { ...this.$auth.user, roles },
        ],
      }
    }
  },
  head: {
    title: 'Projects',
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

<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar ref="toolbar" class="mb-5" :data="projectType" :form="$refs.form" :save="performSave" :delete="performDelete" />

      <s-text-field v-model="projectType.name" label="Name" />
    </v-form>
  </v-container>
</template>

<script>
import EditToolbar from '~/components/EditToolbar.vue'

export default {
  components: { EditToolbar },
  beforeRouteLeave(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  beforeRouteUpdate(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  async asyncData({ $axios, params }) {
    return {
      projectType: await $axios.$get(`/projecttypes/${params.projectTypeId}/`),
    }
  },
  methods: {
    async performSave() {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: this.projectType, fields: ['name'] });
    },
    async performDelete() {
      await this.$store.dispatch('projecttypes/delete', this.projectType);
      this.$router.push({ path: '/designer/' });
    }
  }
}
</script>

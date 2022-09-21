<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :form="$refs.form">
        <copy-button v-if="$auth.hasScope('designer')" :copy="performCopy">
          <template #tooltip>Duplicate Design</template>
        </copy-button>
      </edit-toolbar>

      <s-text-field
        v-model="projectType.name" 
        label="Name"
        :disabled="readonly"
        class="mt-4"
      />
      <language-selection v-model="projectType.language" :disabled="readonly" />
    </v-form>
  </v-container>
</template>

<script>
import EditToolbar from '~/components/EditToolbar.vue'
import LanguageSelection from '~/components/LanguageSelection.vue';
import LockEditMixin from '~/mixins/LockEditMixin';

function getProjectTypeUrl(params) {
  return `/projecttypes/${params.projectTypeId}/`;
}

export default {
  components: { EditToolbar, LanguageSelection },
  mixins: [LockEditMixin],
  async asyncData({ $axios, params }) {
    return {
      projectType: await $axios.$get(getProjectTypeUrl(params)),
    }
  },
  computed: {
    data() {
      return this.projectType;
    },
    deleteConfirmInput() {
      return this.projectType.name;
    },
  },
  methods: {
    getBaseUrl(data) {
      return getProjectTypeUrl({ projectTypeId: data.id });
    },
    getHasEditPermissions() {
      return this.$auth.hasScope('designer');
    },
    async performSave(data) {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: data, fields: ['name'] });
    },
    async performDelete(data) {
      await this.$store.dispatch('projecttypes/delete', data);
      this.$router.push({ path: '/designer/' });
    },
    async performCopy() {
      const obj = await this.$axios.$post(`/projecttypes/${this.projectType.id}/copy/`, {});
      this.$router.push(`/designer/${obj.id}/pdfdesigner/`);
    }
  }
}
</script>

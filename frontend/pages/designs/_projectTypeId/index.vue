<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :form="$refs.form">
        <btn-export :export-url="`/projecttypes/${projectType.id}/export/`" :name="'design-' + projectType.name" />
        <template v-if="$auth.hasScope('designer')">
          <btn-copy :copy="performCopy" tooltip-text="Duplicate Design" />
        </template>
      </edit-toolbar>

      <p v-if="projectType.copy_of" class="mt-4">
        This design is a copy
        <s-btn text small :to="`/designs/${projectType.copy_of}/`" nuxt class="ml-1 mr-1">
          <v-icon>mdi-chevron-right-circle-outline</v-icon> show original
        </s-btn>
      </p>
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
import ProjectTypeLockEditMixin from '~/mixins/ProjectTypeLockEditMixin';

export default {
  mixins: [ProjectTypeLockEditMixin],
  computed: {
    deleteConfirmInput() {
      return this.projectType.name;
    },
  },
  methods: {
    async performSave(data) {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: data, fields: ['name', 'language'] });
    },
    async performDelete(data) {
      await this.$store.dispatch('projecttypes/delete', data);
      this.$router.push({ path: '/designs/' });
    },
    async performCopy() {
      const obj = await this.$store.dispatch('projecttypes/copy', {
        id: this.projectType.id,
        scope: 'global',
      });
      this.$router.push(`/designs/${obj.id}/pdfdesigner/`);
    }
  }
}
</script>

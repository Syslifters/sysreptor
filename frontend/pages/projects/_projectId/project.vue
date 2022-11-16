<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar v-bind="toolbarAttrs">
        <template #title>Project <template v-if="project.readonly">(readonly)</template></template>
        <btn-readonly :value="project.readonly" :set-readonly="setReadonly" />
        <btn-export :export-url="`/pentestprojects/${project.id}/export/`" :name="'project-' + project.name" />
        <btn-copy :copy="performCopy" tooltip-text="Duplicate Project" confirm-text="The whole project will be copied including all pentesters, sections, findings and images." />
      </edit-toolbar>

      <s-text-field v-model="project.name" label="Name" :error-messages="serverErrors?.name" :disabled="project.readonly" class="mt-4" />
      <!-- TODO: how to display linked designs for project in list? @christoph
        * project can have multiple designs: e.g. imported design and customized design
        * user should be able to switch back from a customized design to the imported design or global design (easiest via dropdown, chain of previous designs is not stored in DB)
        * copy project with customized design: copy design or keep reference?
      -->
      <project-type-selection v-model="project.project_type" :error-messages="serverErrors?.project_type" :disabled="project.readonly" />
      <language-selection v-model="project.language" :error-messages="serverErrors?.language" :disabled="project.readonly" />
      <user-selection 
        v-model="project.pentesters" 
        :prevent-unselecting-self="true" 
        :required="true"
        :multiple="true" 
        :error-messages="serverErrors?.pentesters"
        :disabled="project.readonly"
        class="mt-4"
      />
      <user-selection
        v-if="project.imported_pentesters.length > 0"
        v-model="project.imported_pentesters"
        :selectable-users="project.imported_pentesters"
        :multiple="true"
        :disabled="true"
        label="Pentesters (imported)"
        hint="These users do not exist on this instance, they were imported from somewhere else. They do not have access, but can be included in reports."
        class="mt-4"
      />
    </v-form>
  </v-container>
</template>

<script>
import { cloneDeep } from 'lodash';

export default {
  beforeRouteLeave(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  beforeRouteUpdate(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  async asyncData({ params, $axios }) {
    return {
      project: await $axios.$get(`/pentestprojects/${params.projectId}/`)
    };
  },
  data() {
    return {
      serverErrors: null,
    }
  },
  computed: {
    toolbarAttrs() {
      return {
        ref: 'toolbar',
        data: this.project,
        form: this.$refs.form,
        ...(!this.project.readonly ? {
          save: this.performSave,
          delete: this.performDelete,
          deleteConfirmInput: this.project.name,
        } : {}),
      }
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
    async setReadonly(val) {
      await this.$axios.$patch(`/pentestprojects/${this.project.id}/readonly/`, {
        readonly: val,
      });
      // update in store
      const storeProject = cloneDeep(this.project);
      storeProject.readonly = val;
      this.$store.commit('projects/set', storeProject);

      this.$refs.toolbar.resetComponent();
      this.$nuxt.refresh();
    },
    async performCopy() {
      const obj = await this.$store.dispatch('projects/copy', { id: this.project.id });
      this.$router.push({ path: `/projects/${obj.id}/project/` });
    },
    async performDelete() {
      await this.$store.dispatch('projects/delete', this.project);
      this.$router.push({ path: '/projects/' });
    },
  }
}
</script>

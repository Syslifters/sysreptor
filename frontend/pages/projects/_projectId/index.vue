<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar v-bind="toolbarAttrs">
        <template #title>Project</template>
        <btn-readonly :value="project.readonly" :set-readonly="setReadonly" />
        <s-btn
          v-if="project.readonly && archivingEnabled"
          :to="`/projects/${project.id}/archive/`" nuxt
          color="secondary"
          class="mr-1"
        >
          <v-icon>mdi-folder-lock-outline</v-icon>
          Archive
        </s-btn>
        <btn-export 
          :export-url="`/pentestprojects/${project.id}/export/`" 
          :export-all-url="`/pentestprojects/${project.id}/export/all/`"
          :name="'project-' + project.name" 
        />
        <btn-copy :copy="performCopy" tooltip-text="Duplicate Project" confirm-text="The whole project will be copied including all members, sections, findings and images." />
      </edit-toolbar>

      <p v-if="project.copy_of" class="mt-4">
        This project is a copy
        <s-btn text small :to="`/projects/${project.copy_of}/reporting/`" nuxt class="ml-1 mr-1">
          <v-icon>mdi-chevron-right-circle-outline</v-icon> show original
        </s-btn>
      </p>

      <s-text-field v-model="project.name" label="Name" :error-messages="serverErrors?.name" :disabled="project.readonly" class="mt-4" />

      <project-type-selection 
        :value="projectType || project.project_type"
        @input="projectType = $event"
        :query-filters="{scope: ['global', 'private', 'project'], linked_project: project.id}" 
        :error-messages="serverErrors?.project_type" 
        :disabled="project.readonly" 
        :append-link="true"
        return-object
      >
        <template #message="{message}">
          {{ message }}
          <template v-if="message === 'Designs have incompatible field definitions. Converting might result in data loss.'">
            <btn-confirm 
              :action="forceChangeDesign"
              button-text="Force change"
              button-color="error"
              tooltip-text="Force change Design"
              dialog-text="Force change the Design for this project. WARNING: Data of incompatible fields might get lost."
              color="error"
              text
              x-small
            />
            <btn-copy 
              :copy="() => performCopy({project_type: project.project_type})" 
              button-text="Duplicate"
              tooltip-text="Duplicate Project and change Design" 
              confirm-text="The whole project will be copied including all sections, findings and images. All changes are made in the duplicated project. No data will be lost." 
              text
              x-small
              :button-icon="null"
            />
          </template>
        </template>
      </project-type-selection>
      <language-selection v-model="project.language" :error-messages="serverErrors?.language" :disabled="project.readonly" />

      <s-tags 
        v-model="project.tags"
        :disabled="project.readonly"
      />

      <member-selection 
        v-model="project.members" 
        :prevent-unselecting-self="true" 
        :error-messages="serverErrors?.members"
        :disabled="project.readonly"
        :required="true"
        label="Members"
      />

      <member-selection
        v-if="project.imported_members.length > 0"
        v-model="project.imported_members"
        :selectable-users="project.imported_members"
        :disabled="project.readonly"
        :disable-add="true"
        label="Members (imported)"
        hint="These users do not exist on this instance, they were imported from somewhere else. They do not have access, but can be included in reports."
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
    const project = await $axios.$get(`/pentestprojects/${params.projectId}/`);
    return {
      project,
    };
  },
  data() {
    return {
      serverErrors: null,
      projectType: null,
    };
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
    },
    archivingEnabled() {
      return this.$store.getters['apisettings/settings'].features.archiving;
    },
  },
  watch: {
    projectType(val) {
      this.project.project_type = val?.id;
    },
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
    async forceChangeDesign() {
      try {
        this.project.force_change_project_type = true;
        await this.$refs.toolbar.save();
        this.project.force_change_project_type = false;
        this.$refs.toolbar.resetComponent();
      } finally {
        this.project.force_change_project_type = false;
      }
    },
    async setReadonly(val) {
      await this.$store.dispatch('projects/setReadonly', { projectId: this.project.id, readonly: val });
      this.$refs.toolbar.resetComponent();
      this.$nuxt.refresh();
    },
    async performCopy(data = {}) {
      const obj = await this.$store.dispatch('projects/copy', { id: this.project.id, ...data });
      this.$refs.toolbar.resetComponent();
      this.$router.push({ path: `/projects/${obj.id}/` });
    },
    async performDelete() {
      await this.$store.dispatch('projects/delete', this.project);
      this.$router.push({ path: '/projects/' });
    },
  }
}
</script>

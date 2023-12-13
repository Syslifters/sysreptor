<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="finding && project && projectType" :key="project.id + finding.id">
      <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
        <template #context-menu>
          <v-list-item
            :to="{path: '/templates/fromfinding/', query: {project: project.id, finding: finding.id}}"
            prepend-icon="mdi-view-compact"
            title="Save as template"
            :disabled="!auth.permissions.template_editor"
          />
        </template>

        <s-btn-icon
          v-if="finding.template"
          :to="`/templates/${finding.template}/`"
          target="_blank"
          class="ml-1 mr-1"
        >
          <v-icon icon="mdi-view-compact" />
          <s-tooltip activator="parent" text="This finding was created from a template: show template" />
        </s-btn-icon>
        <div class="status-container ml-1 mr-1">
          <s-status-selection v-model="finding.status" :disabled="readonly" />
        </div>
        <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
          <s-user-selection
            v-model="finding.assignee"
            :selectable-users="project.members"
            :disabled="readonly"
            label="Assignee"
            variant="underlined"
            density="compact"
          />
        </div>

        <btn-history v-model="historyVisible" />
      </edit-toolbar>

      <project-history-timeline
        v-model="historyVisible"
        :project="project"
        :finding="finding"
        :current-url="route.fullPath"
      />

      <div v-for="fieldId in projectType.finding_field_order" :key="fieldId">
        <dynamic-input-field
          v-model="finding.data[fieldId]"
          :disabled="readonly"
          :id="fieldId"
          :definition="projectType.finding_fields[fieldId]"
          :autofocus="fieldId === 'title'"
          v-bind="inputFieldAttrs"
        />
      </div>
    </div>
  </fetch-loader>
</template>

<script setup lang="ts">
const auth = useAuth();
const route = useRoute();
const projectStore = useProjectStore();

const { data: finding, project, projectType, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit({
  baseUrl: `/api/v1/pentestprojects/${route.params.projectId}/findings/${route.params.findingId}/`,
  fetchProjectType: true,
  performSave: projectStore.updateFinding,
  performDelete: async (project, finding) => {
    await projectStore.deleteFinding(project, finding);
    await navigateTo(`/projects/${project.id}/reporting/`);
  },
  updateInStore: projectStore.setFinding,
  autoSaveOnUpdateData({ oldValue, newValue }): boolean {
    return oldValue.status !== newValue.status ||
        oldValue.assignee?.id !== newValue.assignee?.id ||
        oldValue.data.cvss !== newValue.data.cvss;
  }
});
const historyVisible = ref(false);
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
.assignee-container {
  width: 17em;
}
</style>

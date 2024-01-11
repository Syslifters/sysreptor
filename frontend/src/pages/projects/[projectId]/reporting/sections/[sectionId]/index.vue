<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="section && project && projectType" :key="project.id + section.id">
      <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
        <div class="status-container ml-1 mr-1">
          <s-status-selection v-model="section.status" :readonly="readonly" />
        </div>
        <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
          <s-user-selection
            v-model="section.assignee"
            :selectable-users="project.members"
            :readonly="readonly"
            label="Assignee"
            variant="underlined"
            density="compact"
          />
        </div>

        <btn-history v-model="historyVisible" />
      </edit-toolbar>

      <history-timeline-project
        v-model="historyVisible"
        :project="project"
        :section="section"
        :current-url="route.fullPath"
      />

      <div v-for="fieldId in section.fields" :key="fieldId">
        <dynamic-input-field
          v-model="section.data[fieldId]"
          :readonly="readonly"
          :id="fieldId"
          :definition="projectType.report_fields[fieldId]"
          v-bind="inputFieldAttrs"
        />
      </div>
    </div>
  </fetch-loader>
</template>

<script setup lang="ts">
const route = useRoute();
const projectStore = useProjectStore();

const { data: section, project, projectType, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit({
  baseUrl: `/api/v1/pentestprojects/${route.params.projectId}/sections/${route.params.sectionId}/`,
  fetchProjectType: true,
  performSave: projectStore.updateSection,
  updateInStore: projectStore.setSection,
  autoSaveOnUpdateData({ oldValue, newValue }): boolean {
    return oldValue.status !== newValue.status || oldValue.assignee?.id !== newValue.assignee?.id;
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

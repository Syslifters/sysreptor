<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="section && project && projectType" :key="project.id + section.id">
      <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
        <div class="status-container ml-1 mr-1">
          <s-status-selection v-model="section.status" :disabled="readonly" />
        </div>
        <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
          <s-user-selection
            v-model="section.assignee"
            :selectable-users="project.members"
            :disabled="readonly"
            label="Assignee"
            variant="underlined"
            density="compact"
          />
        </div>

        <s-btn
          @click="historyVisible = !historyVisible"
          color="secondary"
          prepend-icon="mdi-history"
        >
          <span class="d-none d-lg-inline">Version History</span>
        </s-btn>
      </edit-toolbar>

      <project-history-timeline
        v-model="historyVisible"
        :project="project"
        :section="section"
        :current-url="route.fullPath"
      />

      <div v-for="fieldId in section.fields" :key="fieldId">
        <dynamic-input-field
          v-model="section.data[fieldId]"
          :disabled="readonly"
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

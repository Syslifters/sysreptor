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

        <s-btn-secondary
          v-if="currentUrl"
          :to="currentUrl" exact
          class="ml-1 mr-1 d-none d-lg-inline-flex"
          prepend-icon="mdi-undo"
          text="Back to current version"
        />
        <btn-history v-model="historyVisible" />
      </edit-toolbar>

      <project-history-timeline
        v-model="historyVisible"
        :project="project"
        :section="section"
        :current-url="currentUrl"
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

const { data: section, project, projectType, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit<ReportSection>({
  baseUrl: `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/sections/${route.params.sectionId}/`,
  fetchProjectType: true,
  historyDate: route.params.historyDate as string,
});
const historyVisible = ref(false);
const currentUrl = computed(() => {
  if (project.value && section.value && projectStore.sections(project.value.id).map(s => s.id).includes(section.value.id)) {
    return `/projects/${project.value.id}/reporting/sections/${section.value.id}/`;
  }
  return null;
});
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
.assignee-container {
  width: 17em;
}
</style>

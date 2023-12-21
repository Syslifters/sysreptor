<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="finding && project && projectType" :key="project.id + finding.id">
      <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
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

        <s-btn-secondary
          v-if="currentUrl"
          :to="currentUrl" exact
          class="ml-1 mr-1 d-none d-lg-inline-flex"
          prepend-icon="mdi-undo"
          text="Back to current version"
        />
        <btn-history v-model="historyVisible" />
      </edit-toolbar>

      <history-timeline-project
        v-model="historyVisible"
        :project="project"
        :finding="finding"
        :current-url="currentUrl"
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
const route = useRoute();
const projectStore = useProjectStore();

const { data: finding, project, projectType, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit<PentestFinding>({
  baseUrl: `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/findings/${route.params.findingId}/`,
  fetchProjectType: true,
  historyDate: route.params.historyDate as string,
});
const historyVisible = ref(false);
const currentUrl = computed(() => {
  if (project.value && finding.value && projectStore.findings(project.value.id).map(f => f.id).includes(finding.value.id)) {
    return `/projects/${project.value.id}/reporting/findings/${finding.value.id}/`;
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

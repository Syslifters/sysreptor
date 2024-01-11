<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="section && fetchState.data.value">
      <edit-toolbar v-bind="toolbarAttrs">
        <div class="status-container ml-1 mr-1">
          <s-status-selection v-model="section.status" :disabled="true" />
        </div>
        <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
          <s-user-selection
            v-model="section.assignee"
            :selectable-users="fieldAttrsHistoric.selectableUsers"
            :disabled="true"
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
        :project="fetchState.data.value.projectHistoric"
        :section="section"
        :current-url="currentUrl"
      />

      <v-row class="mt-0">
        <v-col cols="6" class="pb-0">
          <h2 class="text-h5 text-center">Historic Version <chip-date :value="(route.params.historyDate as string)" /></h2>
        </v-col>
        <v-col cols="6" class="pb-0">
          <h2 class="text-h5 text-center">Current Version</h2>
        </v-col>
      </v-row>
      <div v-for="f in diffFieldProps" :key="f.id">
        <dynamic-input-field-diff v-bind="f" />
      </div>
    </div>
  </fetch-loader>
</template>

<script setup lang="ts">
const route = useRoute();
const projectStore = useProjectStore();

const { obj: section, fetchState, fetchLoaderAttrs, toolbarAttrs, fieldAttrsHistoric, fieldAttrsCurrent } = useProjectHistory<ReportSection>({
  subresourceUrlPart: `/sections/${route.params.sectionId}/`,
});
const diffFieldProps = computed(() => formatHistoryObjectFieldProps({
  historic: {
    value: fetchState.data.value?.dataHistoric?.data,
    definition: fetchState.data.value?.projectTypeHistoric?.report_fields,
    fieldIds: fetchState.data.value?.dataHistoric?.fields || [],
    attrs: fieldAttrsHistoric.value,
  },
  current: {
    value: fetchState.data.value?.dataCurrent?.data,
    definition: fetchState.data.value?.projectTypeCurrent?.report_fields,
    fieldIds: fetchState.data.value?.dataCurrent?.fields || [],
    attrs: fieldAttrsCurrent.value,
  },
}));

const historyVisible = ref(false);
const currentUrl = computed(() => {
  if (section.value && projectStore.sections(section.value.project).map(s => s.id).includes(section.value.id)) {
    return `/projects/${section.value.project}/reporting/sections/${section.value.id}/`;
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

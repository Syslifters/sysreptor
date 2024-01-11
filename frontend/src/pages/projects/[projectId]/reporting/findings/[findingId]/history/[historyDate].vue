<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="finding && fetchState.data.value">
      <edit-toolbar v-bind="toolbarAttrs">
        <div class="status-container ml-1 mr-1">
          <s-status-selection v-model="finding.status" :readonly="true" />
        </div>
        <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
          <s-user-selection
            v-model="finding.assignee"
            :selectable-users="fieldAttrsHistoric.selectableUsers"
            :readonly="true"
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
        :finding="finding"
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

const { obj: finding, fetchState, fetchLoaderAttrs, toolbarAttrs, fieldAttrsHistoric, fieldAttrsCurrent } = useProjectHistory<PentestFinding>({
  subresourceUrlPart: `/findings/${route.params.findingId}/`,
});
const diffFieldProps = computed(() => formatHistoryObjectFieldProps({
  historic: {
    value: fetchState.data.value?.dataHistoric?.data,
    definition: fetchState.data.value?.projectTypeHistoric?.finding_fields,
    fieldIds: fetchState.data.value?.projectTypeHistoric?.finding_field_order || [],
    attrs: fieldAttrsHistoric.value,
  },
  current: {
    value: fetchState.data.value?.dataCurrent?.data,
    definition: fetchState.data.value?.projectTypeCurrent?.finding_fields,
    fieldIds: fetchState.data.value?.projectTypeCurrent?.finding_field_order || [],
    attrs: fieldAttrsCurrent.value,
  },
}));

const historyVisible = ref(false);
const currentUrl = computed(() => {
  if (finding.value && projectStore.findings(finding.value.project).map(f => f.id).includes(finding.value.id)) {
    return `/projects/${finding.value.project}/reporting/findings/${finding.value.id}/`;
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

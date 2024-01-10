<template>
  <div>
    <edit-toolbar v-bind="toolbarAttrs">
      <div class="status-container ml-1 mr-1">
        <s-status-selection v-model="finding.status" :disabled="true" />
      </div>
      <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
        <s-user-selection
          v-model="finding.assignee"
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
      :project="fetchState.projectHistoric"
      :finding="finding"
      :current-url="currentUrl"
    />

    <v-row class="mt-0">
      <v-col cols="6" class="pb-0">
        <h2 class="text-h5 text-center">Historic Version</h2>
      </v-col>
      <v-col cols="6" class="pb-0">
        <h2 class="text-h5 text-center">Current Version</h2>
      </v-col>
    </v-row>
    <div v-for="f in diffFieldProps" :key="f.id">
      <dynamic-input-field-diff v-bind="f" />
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute();
const projectStore = useProjectStore();

const { obj: finding, fetchState, toolbarAttrs, fieldAttrsHistoric, fieldAttrsCurrent } = await useProjectHistory<PentestFinding>({
  subresourceUrlPart: `/findings/${route.params.findingId}/`,
});
const diffFieldProps = computed(() => {
  const out = [];
  for (const fieldId of fetchState.value.projectTypeHistoric.finding_field_order) {
    out.push({
      id: fieldId,
      historic: {
        value: fetchState.value.dataHistoric?.data?.[fieldId],
        definition: fetchState.value.projectTypeHistoric.finding_fields[fieldId],
        ...fieldAttrsHistoric.value,
      },
      current: {
        value: fetchState.value.dataCurrent?.data?.[fieldId],
        definition: fetchState.value.projectTypeCurrent?.finding_fields?.[fieldId],
        ...fieldAttrsCurrent.value,
      },
    });
  }
  for (const fieldId of fetchState.value.projectTypeCurrent.finding_field_order) {
    if (!fetchState.value.projectTypeHistoric.finding_field_order.includes(fieldId)) {
      out.push({
        id: fieldId,
        historic: {
          value: null,
          definition: null,
          ...fieldAttrsHistoric.value,
        },
        current: {
          value: fetchState.value.dataCurrent?.data?.[fieldId],
          definition: fetchState.value.projectTypeCurrent?.finding_fields?.[fieldId],
          ...fieldAttrsCurrent.value,
        },
      });
    }
  }
  return out;
})

const historyVisible = ref(false);
const currentUrl = computed(() => {
  if (projectStore.findings(finding.value.project).map(f => f.id).includes(finding.value.id)) {
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

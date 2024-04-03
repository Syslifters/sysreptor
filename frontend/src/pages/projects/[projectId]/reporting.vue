<template>
  <split-menu v-model="localSettings.reportInputMenuSize">
    <template #menu>
      <v-list density="compact" class="pb-0 pt-0 h-100 d-flex flex-column">
        <div class="flex-grow-1 overflow-y-auto">
          <v-list-subheader title="Sections" class="mt-0" />
          <v-list-item
            v-for="section in sections"
            :key="section.id"
            :to="`/projects/${$route.params.projectId}/reporting/sections/${section.id}/`"
            density="compact"
          >
            <template #default>
              <v-list-item-title class="text-body-2">{{ section.label }}</v-list-item-title>
              <v-list-item-subtitle>
                <span v-if="section.assignee" :class="{'assignee-self': section.assignee.id == auth.user.value!.id}">
                  @{{ section.assignee.username }}
                </span>
              </v-list-item-subtitle>
            </template>
            <template #append>
              <s-status-info :value="section.status" />
            </template>
          </v-list-item>

          <v-list-subheader>
            <span>Findings</span>
            <s-btn-icon
              @click="($refs.createFindingDialogRef as any)!.open()"
              :disabled="project.readonly"
              size="small"
              variant="flat"
              color="secondary"
              density="compact"
              class="ml-2"
            >
              <v-icon icon="mdi-plus" />
              <s-tooltip activator="parent" location="top">Add Finding (Ctrl+J)</s-tooltip>
            </s-btn-icon>
            <v-spacer />
            <s-btn-icon
              v-if="projectType.finding_ordering.length > 0"
              @click="toggleOverrideFindingOrder"
              :disabled="project.readonly"
              size="small"
              density="compact"
            >
              <v-icon :icon="project.override_finding_order ? 'mdi-sort-variant-off' : 'mdi-sort-variant'" />
              <s-tooltip activator="parent" location="top">
                <span v-if="project.override_finding_order">Custom order</span>
                <span v-else>Default order</span>
              </s-tooltip>
            </s-btn-icon>
          </v-list-subheader>

          <draggable
            :model-value="findings"
            @update:model-value="sortFindings"
            item-key="id"
            handle=".draggable-handle"
            :disabled="project.readonly || !sortFindingsManual"
          >
            <template #item="{element: finding}">
              <v-list-item
                :to="`/projects/${$route.params.projectId}/reporting/findings/${finding.id}/`"
                :ripple="false"
                density="compact"
                :class="'finding-level-' + riskLevel(finding)"
              >
                <template #prepend>
                  <div v-if="sortFindingsManual" class="draggable-handle mr-2">
                    <v-icon :disabled="project.readonly" icon="mdi-drag-horizontal" />
                  </div>
                </template>
                <template #default>
                  <v-list-item-title class="text-body-2">{{ finding.data.title }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <span v-if="finding.assignee" :class="{'assignee-self': finding.assignee.id == auth.user.value!.id}">
                      @{{ finding.assignee.username }}
                    </span>
                  </v-list-item-subtitle>
                </template>
                <template #append>
                  <s-status-info :value="finding.status" />
                </template>
              </v-list-item>
            </template>
          </draggable>
        </div>

        <div>
          <v-divider class="mb-1" />
          <v-list-item>
            <create-finding-dialog ref="createFindingDialogRef" :project="project" />
          </v-list-item>
        </div>
      </v-list>
    </template>

    <template #default>
      <nuxt-page />
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";
import { scoreFromVector, levelNumberFromScore, levelNumberFromLevelName } from "~/utils/cvss";

definePageMeta({
  title: 'Reporting'
});

const route = useRoute();
const auth = useAuth();
const localSettings = useLocalSettings();
const projectStore = useProjectStore()
const projectTypeStore = useProjectTypeStore();

const project = await useAsyncDataE(async () => await projectStore.fetchById(route.params.projectId as string), { key: 'reporting:project' });
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type), { key: 'reporting:projectType' });
const findings = computed(() => projectStore.findings(project.value.id, { projectType: projectType.value }));
const sections = computed(() => projectStore.sections(project.value.id));
const sortFindingsManual = computed(() => project.value.override_finding_order || projectType.value.finding_ordering.length === 0);

// Periodically refresh lists. Updates project, sections, findings in store
async function refreshListings() {
  try {
    project.value = await projectStore.fetchById(project.value.id);
    projectType.value = await projectTypeStore.getById(project.value.project_type);
  } catch (error) {
    // hide error
  }
}
const refreshListingsInterval = ref();
onMounted(() => {
  refreshListingsInterval.value = setInterval(refreshListings, 10_000);
});
onBeforeUnmount(() => {
  if (refreshListingsInterval.value) {
    clearInterval(refreshListingsInterval.value);
    refreshListingsInterval.value = undefined;
  }
});

// Sort findings
const wasOverrideFindingOrder = ref(false);
watch(sortFindingsManual, () => {
  wasOverrideFindingOrder.value ||= sortFindingsManual.value;
}, { immediate: true });
async function sortFindings(findings: PentestFinding[]) {
  await projectStore.sortFindings(project.value, findings);
}
async function toggleOverrideFindingOrder() {
  if (!wasOverrideFindingOrder.value) {
    // Use current sort order as starting point
    // But prevent destroying previous overwritten order on toggle
    await sortFindings(findings.value);
  }

  project.value = await projectStore.partialUpdateProject({
    id: project.value.id,
    override_finding_order: !project.value.override_finding_order
  } as PentestProject, ['override_finding_order']);
}

function riskLevel(finding: PentestFinding) {
  if ('severity' in projectType.value.finding_fields) {
    return levelNumberFromLevelName(finding.data.severity);
  } else if ('cvss' in projectType.value.finding_fields) {
    return levelNumberFromScore(scoreFromVector(finding.data.cvss));
  } else {
    return 'unknown';
  }
}
</script>

<style lang="scss" scoped>
@use "assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map-get(settings.$risk-color-levels, $level);
  }
}

:deep(.v-list-item-subtitle) {
  font-size: x-small !important;
}

.draggable-handle {
  cursor: grab;

  &:deep(.v-icon) {
    cursor: inherit;
  }
}

:deep(.v-list-subheader) {
  margin-top: 1em;
  padding-left: 0.5em !important;

  .v-list-subheader__text {
    display: flex;
    flex-direction: row;
    width: 100%;
  }
}
</style>

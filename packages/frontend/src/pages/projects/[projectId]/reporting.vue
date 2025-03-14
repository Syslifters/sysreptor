<template>
  <split-menu v-model="localSettings.reportInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <v-list density="compact" class="pb-0 pt-0 h-100 d-flex flex-column">
        <v-list-subheader v-if="isInSearchMode" class="mt-0 pr-2">
          <s-text-field 
            v-model="reportingCollab.search.value"
            placeholder="Search..."
            density="compact"
            variant="underlined"
            prepend-inner-icon="mdi-magnify"
            append-inner-icon="$clear"
            @click:append-inner="hideSearch"
            autofocus
            autocomplete="off"
            spellcheck="false"
          >
            <template #prepend-inner-icon>
              <v-icon icon="mdi-magnify" size="small" />
            </template>
            <template #append-inner-icon>
              <v-icon icon="mdi-close" size="small" />
            </template>
          </s-text-field>
        </v-list-subheader>
        <div v-if="!(isInSearchMode && (reportingCollab.search.value?.length || 0) >= 3)" class="flex-grow-1 overflow-y-auto">
          <v-list-subheader class="mt-0 pr-2">
            <span>Sections</span>
            <v-spacer />
            <s-btn-icon
              v-if="!isInSearchMode"
              @click="showSearch"
              icon="mdi-magnify"
              size="small"
              density="compact"
              class="ml-2"
            />
          </v-list-subheader>
          <v-list-item
            v-for="section in sections"
            :key="section.id"
            :to="sectionUrl(section)"
            :active="router.currentRoute.value.path.startsWith(sectionUrl(section))"
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
              <collab-avatar-group 
                :collab="collabSubpath(reportingCollab.collabProps.value, `sections.${section.id}`)"
                :class="{'mr-2': section.status !== ReviewStatus.IN_PROGRESS}"
              />
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
              :disabled="readonly"
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

          <finding-sidebar-list
            :model-value="findings"
            @update:model-value="sortFindings"
            @create="data => ($refs.createFindingDialogRef as any)!.open(data)"
            :project-type="projectType"
            :override-finding-order="project.override_finding_order"
            :readonly="readonly"
            :to-prefix="`/projects/${route.params.projectId}/reporting/findings/`"
            :collab="reportingCollab.collabProps.value"
            @collab="reportingCollab.onCollabEvent"
          >
            <template #finding-subtitle="{ finding }">
              <v-list-item-subtitle v-if="finding.assignee">@{{ finding.assignee.username }}</v-list-item-subtitle>
            </template>
            <template #finding-item-append="{ finding }">
              <collab-avatar-group
                :collab="collabSubpath(reportingCollab.collabProps.value, `findings.${finding.id}`)"
                :class="{'mr-2': finding.status !== ReviewStatus.IN_PROGRESS}"
              />
              <s-status-info :value="finding.status" />
            </template>
          </finding-sidebar-list>
        </div>

        <div v-else>
          <!-- Search result list -->
          <template v-if="searchResultsSections.length > 0">
            <v-list-subheader title="Sections" class="mt-0 pr-2" />
            <div
              v-for="result in searchResultsSections"
              :key="result.item.id"
            >
              <v-list-item
                :to="sectionUrl(result.item)"
                :active="router.currentRoute.value.path.startsWith(sectionUrl(result.item))"
                density="compact"
              >
                <template #default>
                  <v-list-item-title class="text-body-2">{{ result.item.label }}</v-list-item-title>
                </template>
              </v-list-item>
              <search-match-list 
                :result="result"
                :to-prefix="sectionUrl(result.item)"
                class="match-list"
              />
            </div>
          </template>

          <template v-if="searchResultsFindings.length > 0">
            <v-list-subheader title="Findings" />
            <finding-sidebar-list
              :model-value="searchResultsFindings.map(r => r.item)"
              :project-type="projectType"
              :override-finding-order="project.override_finding_order"
              :readonly="true"
              :hide-drag-handle="true"
              :disable-grouping="true"
            >
              <template #finding-append="{ finding }">
                <search-match-list 
                  :result="searchResultsFindings.find(r => r.item.id === finding.id)!"
                  :to-prefix="`/projects/${route.params.projectId}/reporting/findings/${finding.id}/`"
                  class="match-list"
                />
              </template>
            </finding-sidebar-list>
          </template>
        </div>

        <div v-if="!isInSearchMode">
          <v-divider class="mb-1" />
          <v-list-item>
            <create-finding-dialog ref="createFindingDialogRef" :project="project" />
          </v-list-item>
        </div>
      </v-list>
    </template>

    <template #default>
      <collab-loader :collab="reportingCollab">
        <nuxt-page />
      </collab-loader>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { collabSubpath, ReviewStatus, type PentestFinding, type ReportSection } from '#imports';

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const localSettings = useLocalSettings();
const projectStore = useProjectStore()
const projectTypeStore = useProjectTypeStore();

definePageMeta({
  title: 'Reporting'
});

const project = await useAsyncDataE(async () => await projectStore.fetchById(route.params.projectId as string), { key: 'reporting:project' });
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type), { key: 'reporting:projectType' });
const findings = computed(() => projectStore.findings(project.value.id, { projectType: projectType.value }));
const sections = computed(() => projectStore.sections(project.value.id, { projectType: projectType.value }));
const sortFindingsManual = computed(() => project.value.override_finding_order || projectType.value.finding_ordering.length === 0);

const readonly = computed(() => project.value.readonly || !auth.permissions.value.edit_projects);

const reportingCollab = projectStore.useReportingCollab({ project: project.value });
onMounted(async () => {
  await reportingCollab.connect();
  collabAwarenessSendNavigate();
});
onBeforeUnmount(async () => {
  await reportingCollab.disconnect();
});
watch(() => router.currentRoute.value, collabAwarenessSendNavigate);

function collabAwarenessSendNavigate() {
  const findingId = router.currentRoute.value.params.findingId;
  const sectionId = router.currentRoute.value.params.sectionId;
  reportingCollab.onCollabEvent({
    type: CollabEventType.AWARENESS,
    path: collabSubpath(reportingCollab.collabProps.value, findingId ? `findings.${findingId}` : sectionId ? `sections.${sectionId}` : null).path,
  });
}

function sectionUrl(section: ReportSection) {
  return `/projects/${route.params.projectId}/reporting/sections/${section.id}/`;
}


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
    const findingsSorted = groupFindings({ findings: findings.value, projectType: projectType.value }).flatMap(g => g.findings);
    await sortFindings(findingsSorted);
  }

  project.value = await projectStore.partialUpdateProject({
    id: project.value.id,
    override_finding_order: !project.value.override_finding_order
  } as PentestProject, ['override_finding_order']);
}


// Search
const isInSearchMode = computed(() => reportingCollab.search.value !== null);
const searchResultsSections = computed(() => searchSections(sections.value, projectType.value, reportingCollab.search.value));
const searchResultsFindings = computed(() => searchFindings(findings.value, projectType.value, reportingCollab.search.value));
function showSearch() {
  reportingCollab.search.value = '';
}
function hideSearch() {
  reportingCollab.search.value = null;
}
useKeyboardShortcut('ctrl+shift+f', () => showSearch());


useHeadExtended({
  syncState: reportingCollab.syncState,
});

</script>

<style lang="scss" scoped>
:deep(.v-list-item-subtitle) {
  font-size: x-small !important;
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

.match-list {
  padding-left: 0.75rem;
}
</style>

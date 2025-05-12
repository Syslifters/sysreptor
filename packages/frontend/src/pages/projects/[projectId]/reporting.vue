<template>
  <split-menu v-model="localSettings.reportInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <report-sidebar
        :sections="sections"
        :findings="findings"
        @update:findings="sortFindings"
        @create:finding="createFindingDialogRef?.open"
        v-model:search="reportingCollab.search.value"
        :override-finding-order="project.override_finding_order"
        @update:override-finding-order="toggleOverrideFindingOrder"
        :project-type="projectType"
        :readonly="readonly"
        :to-prefix="`/projects/${route.params.projectId}/reporting/`"
        :collab="reportingCollab.collabProps.value"
        @collab="reportingCollab.onCollabEvent"
      />
      <create-finding-dialog 
        ref="createFindingDialogRef"
        :project="project"
      />
    </template>

    <template #default>
      <collab-loader :collab="reportingCollab">
        <nuxt-page />
      </collab-loader>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { collabSubpath, type PentestFinding } from '#imports';
import type { CreateFindingDialog } from '#components';

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const localSettings = useLocalSettings();
const projectStore = useProjectStore()
const projectTypeStore = useProjectTypeStore();

definePageMeta({
  title: 'Reporting'
});

const project = await useAsyncDataE(async () => await projectStore.fetchById(route.params.projectId as string));
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type));
const findings = computed(() => projectStore.findings(project.value.id));
const sections = computed(() => projectStore.sections(project.value.id));
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

const createFindingDialogRef = useTemplateRef('createFindingDialogRef');

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

useHeadExtended({
  syncState: reportingCollab.syncState,
});
</script>

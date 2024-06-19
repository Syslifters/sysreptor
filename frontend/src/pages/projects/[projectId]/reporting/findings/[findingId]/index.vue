<template>
  <div v-if="finding && project && projectType" :key="project.id + finding.id">
    <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
      <template #context-menu>
        <v-list-item
          :to="{path: '/templates/fromfinding/', query: {project: project.id, finding: finding.id}}"
          prepend-icon="mdi-view-compact"
          title="Save as template"
          :disabled="!auth.permissions.value.template_editor"
        />
      </template>

      <s-btn-icon
        v-if="finding.template"
        :to="`/templates/${finding.template}/`"
        target="_blank"
        class="ml-1 mr-1"
      >
        <v-icon icon="mdi-view-compact" />
        <s-tooltip activator="parent" text="This finding was created from a template: show template" />
      </s-btn-icon>
      <div class="status-container ml-1 mr-1">
        <s-status-selection 
          :model-value="finding.status"
          @update:model-value="updateKey('status', $event)"
          :readonly="readonly" 
        />
      </div>
      <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
        <s-user-selection
          :model-value="finding.assignee"
          @update:model-value="updateKey('assignee', $event)"
          :selectable-users="project.members"
          :readonly="readonly"
          label="Assignee"
          variant="underlined"
          density="compact"
        />
      </div>
      
      <btn-comments v-model="localSettings.reportingCommentSidebarVisible" />
      <btn-history v-model="historyVisible" />
    </edit-toolbar>

    <history-timeline-project
      v-model="historyVisible"
      :project="project"
      :finding="finding"
      :current-url="route.fullPath"
    />

    <div v-for="fieldId in projectType.finding_field_order" :key="fieldId">
      <dynamic-input-field
        :model-value="finding.data[fieldId]"
        :collab="collabSubpath(reportingCollab.collabProps.value, `data.${fieldId}`)"
        @collab="reportingCollab.onCollabEvent"
        @comment="commentSidebarRef?.onCommentEvent"
        :readonly="readonly"
        :id="fieldId"
        :definition="projectType.finding_fields[fieldId]!"
        v-bind="inputFieldAttrs"
      />
    </div>

    <comment-sidebar
      ref="commentSidebarRef"
      :project="project"
      :project-type="projectType"
      :finding-id="route.params.findingId as string"
      :readonly="readonly"
    />
  </div>
</template>

<script setup lang="ts">
import { type CommentSidebar } from '#components';

const auth = useAuth();
const route = useRoute();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string), { key: 'findings:project' });
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type), { key: 'findings:projectType' });

const reportingCollab = projectStore.useReportingCollab({ project: project.value, findingId: route.params.findingId as string });
const finding = computedThrottled(() => reportingCollab.data.value.findings[route.params.findingId as string], { throttle: 500 });
const readonly = computed(() => reportingCollab.readonly.value);

const { inputFieldAttrs, errorMessage } = useProjectEditBase({
  project: computed(() => project.value),
  spellcheckEnabled: computed({ get: () => localSettings.reportingSpellcheckEnabled, set: (val) => { localSettings.reportingSpellcheckEnabled = val } }),
  markdownEditorMode: computed({ get: () => localSettings.reportingMarkdownEditorMode, set: (val) => { localSettings.reportingMarkdownEditorMode = val } }),
});
const toolbarAttrs = computed(() => ({
  data: finding.value,
  errorMessage: errorMessage.value || 
    (!reportingCollab.hasLock.value ? 'This finding is locked by another user. Upgrade to SysReptor Professional for lock-free collaborative editing.' : null),
  delete: async (finding: PentestFinding) => {
    await projectStore.deleteFinding(project.value, finding);
    await navigateTo(`/projects/${project.value.id}/reporting/`);
  },
}));
const historyVisible = ref(false);
const commentSidebarRef = ref<InstanceType<typeof CommentSidebar>>();

function updateKey(key: string, value: any) {
  reportingCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(reportingCollab.collabProps.value, key).path,
    value,
  })
}

useAutofocus(finding, 'title');
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
.assignee-container {
  width: 17em;
}
</style>

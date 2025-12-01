<template>
  <div v-if="finding && project && projectType" :key="project.id + finding.id" class="h-100 d-flex flex-column">
    <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
      <template #context-menu>
        <v-list-item
          :to="{path: '/templates/fromfinding/', query: {project: project.id, finding: finding.id}}"
          prepend-icon="mdi-view-compact"
          :disabled="!auth.permissions.value.template_editor"
        >
          <template #title><permission-info :value="auth.permissions.value.template_editor" permission-name="Template Editor">Save as template</permission-info></template>
        </v-list-item>
        <btn-copy 
          :copy="performCopy"
          :disabled="project.readonly"
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
      <s-assignee-selection
        :model-value="finding.assignee"
        @update:model-value="updateKey('assignee', $event)"
        :selectable-users="project.members"
        :readonly="readonly"
        class="ml-1 mr-1"
      />
      
      <chat-btn v-model="localSettings.reportingSidebarType" />
      <btn-comments v-model="localSettings.reportingSidebarType" :comments="reportingCollab.collabProps.value.comments!" />
      <btn-history v-model="historyVisible" />
    </edit-toolbar>

    <history-timeline-project
      v-model="historyVisible"
      :project="project"
      :finding="finding"
      :current-url="route.fullPath"
    />

    <v-container fluid class="pt-0 flex-grow-height overflow-y-auto">
      <dynamic-input-field
        v-for="fieldDefinition in projectType.finding_fields" :key="fieldDefinition.id"
        :model-value="finding.data[fieldDefinition.id]"
        :collab="reportingCollab.collabSubpathProps.value[`data.${fieldDefinition.id}`]"
        @collab="reportingCollab.onCollabEvent"
        @comment="reportingCollab.onCommentEvent"
        @search="reportingCollab.search.value = $event"
        :field-value-suggestions="findingFieldValueSuggestions"
        :readonly="readonly"
        :id="fieldDefinition.id"
        :definition="fieldDefinition"
        v-bind="inputFieldAttrs"
        :data-testid="fieldDefinition.id"
      />
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { collabSubpath } from '#imports';

const auth = useAuth();
const route = useRoute();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string));
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type));

const reportingCollab = projectStore.useReportingCollab({ project, projectType, findingId: route.params.findingId as string });
const finding = computed(() => reportingCollab.data.value.findings[route.params.findingId as string]);
const findingFieldValueSuggestions = useFindingFieldValueSuggestions(reportingCollab.data.value.findings, projectType.value);
const readonly = computed(() => reportingCollab.readonly.value);

const { inputFieldAttrs, errorMessage } = useProjectEditBase({
  project,
  projectType,
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
  canDelete: !project.value.readonly,
}));
const historyVisible = ref(false);

function updateKey(key: string, value: any) {
  reportingCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(reportingCollab.collabProps.value, key).path,
    value,
  })
}

async function performCopy() {
  const obj = await projectStore.copyFinding(project.value, finding.value!);
  await navigateTo(`/projects/${project.value.id}/reporting/findings/${obj.id}/`);
}

useAutofocus(finding, 'title');
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
</style>

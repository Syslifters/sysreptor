<template>
  <div v-if="section && project && projectType" :key="project.id + section.id" class="h-100 d-flex flex-column">
    <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
      <div class="status-container ml-1 mr-1">
        <s-status-selection 
          :model-value="section.status"
          @update:model-value="updateKey('status', $event)"
          :readonly="readonly" 
        />
      </div>
      <s-assignee-selection
        :model-value="section.assignee"
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
      :section="section"
      :current-url="route.fullPath"
    />

    <v-container fluid class="pt-0 flex-grow-height overflow-y-auto">
      <dynamic-input-field
        v-for="fieldDefinition in sectionDefinition.fields" :key="fieldDefinition.id"
        :model-value="section.data[fieldDefinition.id]"
        :collab="reportingCollab.collabSubpathProps.value[`data.${fieldDefinition.id}`]"
        @collab="reportingCollab.onCollabEvent"
        @comment="commentSidebarRef?.onCommentEvent"
        @search="reportingCollab.search.value = $event"
        :readonly="readonly"
        :id="fieldDefinition.id"
        :definition="fieldDefinition"
        v-bind="inputFieldAttrs"
      />
    </v-container>
  </div>
</template>

<script setup lang="ts">
import type { CommentSidebar } from '#components';
import { collabSubpath } from '#imports';

const route = useRoute();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string));
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type));
const sectionDefinition = computed(() => projectType.value.report_sections.find(s => s.id === route.params.sectionId)!);

const reportingCollab = projectStore.useReportingCollab({ project, projectType, sectionId: route.params.sectionId as string });
const section = computed(() => reportingCollab.data.value.sections[route.params.sectionId as string]);
const readonly = computed(() => reportingCollab.readonly.value);

const { inputFieldAttrs, errorMessage } = useProjectEditBase({
  project,
  projectType,
  spellcheckEnabled: computed({ get: () => localSettings.reportingSpellcheckEnabled, set: (val) => { localSettings.reportingSpellcheckEnabled = val } }),
  markdownEditorMode: computed({ get: () => localSettings.reportingMarkdownEditorMode, set: (val) => { localSettings.reportingMarkdownEditorMode = val } }),
});
const toolbarAttrs = computed(() => ({
  data: section.value,
  errorMessage: errorMessage.value || 
    (!reportingCollab.hasLock.value ? 'This section is locked by another user. Upgrade to SysReptor Professional for lock-free collaborative editing.' : null),
}));
const historyVisible = ref(false);
const commentSidebarRef = useTemplateRef<InstanceType<typeof CommentSidebar>>('commentSidebarRef');

function updateKey(key: string, value: any) {
  reportingCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(reportingCollab.collabProps.value, key).path,
    value,
  })
}

useAutofocus(section);
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
.assignee-container {
  width: 17em;
}
</style>

<template>
  <div v-if="section && project && projectType" :key="project.id + section.id">
    <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
      <div class="status-container ml-1 mr-1">
        <s-status-selection 
          :model-value="section.status"
          @update:model-value="updateKey('status', $event)"
          :readonly="readonly" 
        />
      </div>
      <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
        <s-user-selection
          :model-value="section.assignee"
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
      :section="section"
      :current-url="route.fullPath"
    />

    <div v-for="fieldId in section.fields" :key="fieldId">
      <dynamic-input-field
        :model-value="section.data[fieldId]"
        :collab="collabSubpath(reportingCollab.collabProps.value, `data.${fieldId}`)"
        @collab="reportingCollab.onCollabEvent"
        :comment="commentSidebarRef?.commentProps"
        @comment="commentSidebarRef?.onCommentEvent"
        :readonly="readonly"
        :id="fieldId"
        :definition="projectType.report_fields[fieldId]"
        v-bind="inputFieldAttrs"
      />
    </div>

    <comment-sidebar
      ref="commentSidebarRef"
      :project="project"
      :project-type="projectType"
      :section-id="route.params.sectionId as string"
      :readonly="readonly"
    />
  </div>
</template>

<script setup lang="ts">
import { type CommentSidebar } from '#components';

const route = useRoute();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string), { key: 'sections:project' });
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type), { key: 'sections:projectType' });

const reportingCollab = projectStore.useReportingCollab({ project: project.value, sectionId: route.params.sectionId as string });
const section = computedThrottled(() => reportingCollab.data.value.sections[route.params.sectionId as string], { throttle: 500 });
const readonly = computed(() => reportingCollab.readonly.value);

const { inputFieldAttrs, errorMessage } = useProjectEditBase({
  project: computed(() => project.value),
  spellcheckEnabled: computed({ get: () => localSettings.reportingSpellcheckEnabled, set: (val) => { localSettings.reportingSpellcheckEnabled = val } }),
  markdownEditorMode: computed({ get: () => localSettings.reportingMarkdownEditorMode, set: (val) => { localSettings.reportingMarkdownEditorMode = val } }),
});
const toolbarAttrs = computed(() => ({
  data: section.value,
  errorMessage: errorMessage.value || 
    (!reportingCollab.hasLock.value ? 'This section is locked by another user. Upgrade to SysReptor Professional for lock-free collaborative editing.' : null),
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
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
.assignee-container {
  width: 17em;
}
</style>

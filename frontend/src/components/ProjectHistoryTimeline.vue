<template>
  <history-timeline :model-value="props.modelValue" @update:model-value="emit('update:modelValue', $event)" :url="historyTimelineUrl">
    <template #item="{item}">
      <history-timeline-item :value="item" :to="historyItemTo(item)">
        <template #title>
          <span v-if="item.history_change_reason">{{ item.history_change_reason }}</span>
          <span v-else-if="item.history_type === '+'">Created {{ formatModelName(item.history_model) }}</span>
          <span v-else-if="item.history_type === '-'">Deleted {{ formatModelName(item.history_model) }}</span>
        </template>
      </history-timeline-item>
    </template>
  </history-timeline>
</template>

<script setup lang="ts">
import urlJoin from "url-join";

const props = defineProps<{
  modelValue: boolean;
  project: PentestProject;
  finding?: PentestFinding;
  section?: ReportSection;
  note?: ProjectNote;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const historyTimelineUrl = computed(() => {
  let url = '';
  if (props.finding) {
    url = `/findings/${props.finding.id}/`;
  } else if (props.section) {
    url = `/sections/${props.section.id}/`;
  } else if (props.note) {
    url = `/notes/${props.note.id}/`;
  }
  return urlJoin(`/api/v1/pentestprojects/${props.project.id}/`, url, '/history-timeline/');
});
function historyItemTo(historyRecord: HistoryTimelineRecord) {
  const prefix = `/projects/${props.project.id}/`;
  const postfix = `/history/${historyRecord.history_date}/`;
  if (historyRecord.history_model === 'PentestFinding') {
    return urlJoin(prefix, `/reporting/findings/${historyRecord.id}/`, postfix);
  } else if (historyRecord.history_model === 'ReportSection') {
    return urlJoin(prefix, `/reporting/sections/${historyRecord.id}/`, postfix);
  } else if (historyRecord.history_model === 'ProjectNotebookPage') {
    return urlJoin(prefix, `/notes/${historyRecord.id}/`, postfix);
  }
  return null;
}
function formatModelName(model: string) {
  return {
    PentestProject: 'Project',
    PentestFinding: 'Finding',
    ReportSection: 'Section',
    ProjectNotebookPage: 'Note',
    UploadedImage: 'Image',
    UploadedProjectFile: 'File',
    ProjectMemberInfo: 'Member',
  }[model] || model;
}
</script>

<template>
  <history-timeline-item :value="props.item" :to="historyItemTo(props.item)">
    <template #title>
      <span v-if="item.history_change_reason">{{ props.item.history_change_reason }}</span>
      <span v-else-if="props.item.history_type === '+'">Created {{ formatModelName(props.item.history_model) }}</span>
      <span v-else-if="props.item.history_type === '-'">Deleted {{ formatModelName(props.item.history_model) }}</span>
    </template>
    <template #append-infos v-if="props.details">
      <v-chip size="small">
        {{ formatModelName(props.item.history_model) }}
        <span v-if="props.item.history_title">: {{ props.item.history_title }}</span>
      </v-chip>
    </template>
  </history-timeline-item>
</template>

<script setup lang="ts">
import urlJoin from "url-join";

const props = defineProps<{
  item: HistoryTimelineRecord;
  project: PentestProject;
  details: boolean;
}>();

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

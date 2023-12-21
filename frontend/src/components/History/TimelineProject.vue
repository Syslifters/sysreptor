<template>
  <history-timeline :model-value="props.modelValue" @update:model-value="emit('update:modelValue', $event)" :url="historyTimelineUrl">
    <template #item="{item}">
      <history-timeline-item-project :item="item" :project="project" /> 
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
  return urlJoin(`/api/v1/pentestprojects/${props.project.id}/`, url, '/history-timeline/?mode=short');
});
</script>

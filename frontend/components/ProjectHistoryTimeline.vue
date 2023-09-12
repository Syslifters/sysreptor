<template>
  <history-timeline v-bind="$attrs" v-on="$listeners" :url="historyTimelineUrl">
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

<script>
import urlJoin from 'url-join';
export default {
  props: {
    project: {
      type: Object,
      required: true,
    },
    finding: {
      type: Object,
      default: null,
    },
    section: {
      type: Object,
      default: null,
    },
    note: {
      type: Object,
      default: null,
    },
  },
  computed: {
    historyTimelineUrl() {
      let url = '';
      if (this.finding) {
        url = `/findings/${this.finding.id}/`;
      } else if (this.section) {
        url = `/sections/${this.section.id}/`;
      } else if (this.note) {
        url = `/notes/${this.note.id}/`;
      }
      return urlJoin(`/pentestprojects/${this.project.id}/`, url, '/history-timeline/');
    },
  },
  methods: {
    historyItemTo(item) {
      const prefix = `/projects/${this.project.id}/`;
      const postfix = `/history/${item.history_date}/`;
      if (item.history_model === 'PentestFinding') {
        return urlJoin(prefix, `/reporting/findings/${item.id}/`, postfix);
      } else if (item.history_model === 'ReportSection') {
        return urlJoin(prefix, `/reporting/sections/${item.id}/`, postfix);
      } else if (item.history_model === 'ProjectNotebookPage') {
        return urlJoin(prefix, `/notes/${item.id}/`, postfix);
      }
      return null;
    },
    formatModelName(model) {
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
  }
}
</script>

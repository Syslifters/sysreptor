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
export default {
  props: {
    template: {
      type: Object,
      required: true,
    },
    translation: {
      type: Object,
      default: null,
    },
  },
  computed: {
    historyTimelineUrl() {
      const tr = this.translation || this.template.translations.find(tr => tr.is_main);
      let url = `/findingtemplates/${this.template.id}/translations/${tr.id}/history-timeline/`;
      if (tr.is_main) {
        url += '?include_template_timeline=true';
      }
      return url;
    },
  },
  methods: {
    historyItemTo(item) {
      return {
        path: `/templates/${this.template.id}/history/${item.history_date}/`,
        query: {
          translation_id: item.history_model === 'FindingTemplateTranslation' ? item.id : this.template.translations.find(tr => tr.is_main).id,
        }
      };
    },
    formatModelName(model) {
      return {
        FindingTemplate: 'Template',
        FindingTemplateTranslation: 'Translation',
        UploadedTemplateImage: 'Image',
      }[model] || model;
    }
  }
}
</script>

<template>
  <history-timeline :url="historyTimelineUrl">
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
const props = defineProps<{
  template: FindingTemplate;
  translation?: FindingTemplateTranslation;
}>();

const historyTimelineUrl = computed(() => {
  const tr = props.translation || props.template.translations.find(tr => tr.is_main)!;
  let url = `/api/v1/findingtemplates/${props.template.id}/translations/${tr.id}/history-timeline/`;
  if (tr.is_main) {
    url += '?include_template_timeline=true';
  }
  return url;
})

function historyItemTo(item: HistoryTimelineRecord) {
  const translationId = item.history_model === 'FindingTemplateTranslation' ? item.id : props.template.translations.find(tr => tr.is_main)!.id;
  return `/templates/${props.template.id}/history/${item.history_date}/?translation_id=${translationId}`;
}

function formatModelName(model: string) {
  return {
    FindingTemplate: 'Template',
    FindingTemplateTranslation: 'Translation',
    UploadedTemplateImage: 'Image',
  }[model] || model;
}
</script>

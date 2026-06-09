<template>
  <v-list-item-title class="w-100 d-flex" :data-testid="'select-item-' + translation.data.title">
    <chip-cvss :risk-score="translation.risk_score" :risk-level="translation.risk_level" />
    <div class="pt-2 pb-2 flex-grow-1 wrap-content">
      {{ translation.data.title }}
      <br />
      <chip-status v-if="translation.status !== 'finished'" :value="translation.status" />
      <chip-language
        v-for="tr in props.template.translations" :key="tr.id"
        :value="tr.language"
        v-tooltip="{text: tr.data.title}"
      />
      <chip-tag v-for="tag in props.template.tags" :key="tag" :value="tag" />
    </div>
    <v-spacer />
    <s-btn-icon
      :to="{path: `/templates/${props.template.id}/`, query: { language: props.language }}"
      target="_blank"
      icon="mdi-chevron-right-circle"
      v-tooltip="'Show template'"
    />
  </v-list-item-title>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  template: FindingTemplate;
  language?: string|null;
}>(), {
  language: null,
});
const translation = computed(() =>
  props.template.translations.find(tr => tr.language === props.language) ||
    props.template.translations.find(tr => tr.is_main)!);
</script>

<style lang="scss" scoped>
.wrap-content {
  white-space: normal;
}
</style>

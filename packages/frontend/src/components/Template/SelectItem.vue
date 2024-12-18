<template>
  <v-list-item-title class="w-100 d-flex" :data-testid="'select-item-' + translation.data.title">
    <chip-cvss :risk-score="translation.risk_score" :risk-level="translation.risk_level" />
    <div class="pt-2 pb-2 flex-grow-1 wrap-content">
      {{ translation.data.title }}
      <br />
      <chip-review-status v-if="translation.status !== 'finished'" :value="translation.status" />
      <s-tooltip v-for="tr in props.template.translations" :key="tr.id" :text="tr.data.title">
        <template #activator="{props: tooltipProps}">
          <chip-language :value="tr.language" v-bind="tooltipProps" />
        </template>
      </s-tooltip>
      <chip-tag v-for="tag in props.template.tags" :key="tag" :value="tag" />
    </div>
    <v-spacer />
    <s-btn-icon
      :to="{path: `/templates/${props.template.id}/`, query: { language: props.language }}"
      target="_blank"
    >
      <v-icon icon="mdi-chevron-right-circle" />
      <s-tooltip activator="parent" text="Show template" />
    </s-btn-icon>
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
  white-space: normal !important;
}
</style>

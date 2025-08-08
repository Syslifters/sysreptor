<template>
  <v-list-item>
    <v-list-item-title>
      <chip-cvss :risk-score="translation.risk_score" :risk-level="translation.risk_level" />
      {{ translation.data.title }}
    </v-list-item-title>
    <v-list-item-subtitle>
      <chip-status
        :value="translation.status"
        :filterable="true"
        @filter="emit('filter', $event)"
      />
      <s-tooltip v-for="tr in props.template.translations" :key="tr.id">
        <template #activator="{ props: tooltipProps }">
          <chip-language
            :value="tr.language"
            v-bind="tooltipProps"
            :filterable="true"
            @filter="emit('filter', $event)"
          />
        </template>
        <template #default>
          {{ tr.data.title }}
        </template>
      </s-tooltip>
      <chip-tag
        v-for="tag in props.template.tags"
        :key="tag"
        :value="tag"
        :filterable="true"
        @filter="emit('filter', $event)"
      />
    </v-list-item-subtitle>
  </v-list-item>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps <{
  template: FindingTemplate,
  language?: string|null,
}>(), {
  language: null
});
const emit = defineEmits<{
  filter: [filter: FilterValue];
}>();

const translation = computed(() => props.template.translations.find(tr => tr.language === props.language) || props.template.translations.find(tr => tr.is_main)!);


</script>

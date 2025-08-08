<template>
  <component 
    :is="{
      'select': FilterChipSelect,
      'combobox': FilterChipCombobox,
      'timerange': FilterChipTimerange,
      'daterange': FilterChipDaterange,
      'text': FilterChipText,
    }[props.type]"
    v-model:filter="filter"
    :filter-properties="props.filterProperties"
    @remove="emit('remove')"
  />
</template>

<script setup lang="ts">
import { FilterChipCombobox, FilterChipDaterange, FilterChipSelect, FilterChipText, FilterChipTimerange } from '#components';

const filter = defineModel<FilterValue>('filter', { required: true })
const props = defineProps<{
  type: string;
  filterProperties: FilterProperties;
}>();
const emit = defineEmits(['remove']);
</script>

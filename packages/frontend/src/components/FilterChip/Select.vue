<template>
  <filter-chip-base
    v-model:filter="filter"
    :display-value="displayValue"
    :filter-properties="props.filterProperties"
    @remove="emit('remove')"
  >
    <v-select
      v-model="filter.value"
      :label="props.filterProperties.name || filter.id"
      :items="props.filterProperties.options || []"
      item-title="title"
      item-value="value"
      density="compact"
      hide-details="auto"
      variant="outlined"
      :multiple="false"
    />
  </filter-chip-base>
</template>

<script setup lang="ts">
const filter = defineModel<FilterValue>('filter', { required: true })
const props = defineProps<{
  filterProperties: FilterProperties
}>()
const emit = defineEmits(['remove']);

const displayValue = computed(() => {
  if (!filter.value.value) return '';

  const items = props.filterProperties.options || [];
  const selectedItem = items.find(item => {
    if (typeof item === 'string') {
      return item === filter.value.value;
    } else {
      return (item as any).value === filter.value.value;
    }
  });

  if (!selectedItem) return String(filter.value.value);
  
  return typeof selectedItem === 'string' ? selectedItem : (selectedItem as any).title;
});
</script>

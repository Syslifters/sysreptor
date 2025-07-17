<template>
  <filter-chip-base
    v-model:filter="filter"
    :filter-properties="props.filterProperties"
    @remove="emit('remove')"
  >
    <v-combobox
      v-model="filter.value"
      :label="props.filterProperties.name || filter.id"
      :items="props.filterProperties.options || []"
      density="compact"
      hide-details="auto"
      variant="outlined"
      :multiple="typeof filter.value === 'string' ? false : true"
      clearable
    />
  </filter-chip-base>
</template>

<script setup lang="ts">
const filter = defineModel<FilterValue>('filter', { required: true })
const props = defineProps<{
  filterProperties: FilterProperties
}>()
const emit = defineEmits(['remove']);
</script>

<template>
  <div class="d-flex flex-wrap">
    <template v-for="(filter, index) in activeFilters" :key="`${index}-${filter.id}`">
      <filter-chip
        v-if="props.filterProperties.some(f => f.id === filter.id)"
        :filter="filter"
        @update:filter="updateFilterValue(index, $event)"
        :type="props.filterProperties.find(f => f.id === filter.id)!.type"
        :filter-properties="props.filterProperties.find(f => f.id === filter.id)!"
        @remove="updateFilterValue(index, undefined)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
const activeFilters = defineModel<FilterValue[]>({ required: true });
const props = defineProps<{
  filterProperties: FilterProperties[];
}>();

function updateFilterValue(idx: number, value?: FilterValue) {
  if (value === undefined) {
    activeFilters.value = activeFilters.value.filter((_, i) => i !== idx);
  } else {
    const newValue = [...activeFilters.value];
    newValue[idx] = value;
    activeFilters.value = newValue;
  }
}
</script>

<template>
  <div class="d-flex flex-wrap">
    <filter-chip
      v-for="(filter, index) in activeFilters.filter(f => props.filterProperties.some(fp => fp.id === f.id))"
      :key="`${index}-${filter.internalId}`"
      :filter="filter"
      @update:filter="updateFilterValue(index, $event)"
      :is-pinned="filter.isPinned"
      @update:is-pinned="updateIsPinned(index, $event)"
      :type="props.filterProperties.find(f => f.id === filter.id)!.type"
      :filter-properties="props.filterProperties.find(f => f.id === filter.id)!"
      @remove="updateFilterValue(index, undefined)"
    />
  </div>
</template>

<script setup lang="ts">
const activeFilters = defineModel<FilterValue[]>({ required: true });
const props = defineProps<{
  filterProperties: FilterProperties[];
}>();
const emit = defineEmits(['update-pinned']);


function updateFilterValue(idx: number, value?: FilterValue) {
  if (!value) {
    activeFilters.value = activeFilters.value.filter((_, i) => i !== idx);
  } else {
    const newValue = [...activeFilters.value];
    newValue[idx] = value;
    activeFilters.value = newValue;

    if (value.isPinned) {
      emit('update-pinned');
    }
  }
}

function updateIsPinned(idx: number, isPinned: boolean) {
  activeFilters.value = activeFilters.value.map((f, fIdx) => fIdx === idx ? { ...f, isPinned } : f);
  emit('update-pinned');
}
</script>

<template>
  <div class="d-flex flex-wrap">
    <template v-for="(filter, index) in activeFilters" :key="`${index}-${filter.id}`">
      <filter-chip
        v-if="props.filterProperties.some(f => f.id === filter.id)"
        :filter="filter"
        @update:filter="updateFilterValue(index, $event)"
        :type="props.filterProperties.find(f => f.id === filter.id)!.type"
        :filter-properties="props.filterProperties.find(f => f.id === filter.id)!"
        :isPinned="isFilterPinned(filter, props.filterProperties.find(f => f.id === filter.id)!)"
        @pin="onPin"
        @unpin="onUnpin"
        @remove="updateFilterValue(index, undefined)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';

const props = defineProps<{
  filterProperties: FilterProperties[];
  pinnedStrings?: string[];
}>();

const emit = defineEmits(['pin', 'unpin']);

// activeFilters is a model bound from parent
const activeFilters = defineModel<FilterValue[]>({ required: true });

// pinned state is passed from pages via ListView; List-level logic will call parent to update store

function mergePinnedIntoActive() {
  // No-op: pinned filters are applied by ListView as defaults
}

onMounted(() => {
  // Nothing to do here; parent ListView will initialize activeFilters
});

watch(() => props.filterProperties, () => {
  mergePinnedIntoActive();
}, { deep: true });

// Also attempt to merge when parent initializes activeFilters (watch model)
watch(activeFilters, () => {
  // Nothing to do here; parent ListView will control activeFilters initialization
}, { immediate: true, deep: true });

function isFilterPinned(filter: FilterValue, filterProp: FilterProperties) {
  const pinKey = `${filterProp.id}:${JSON.stringify(filter.value)}`;
  return (props.pinnedStrings || []).includes(pinKey);
}

function onPin(pinStr: string) {
  emit('pin', pinStr);
}

function onUnpin(pinStr: string) {
  emit('unpin', pinStr);
}

function updateFilterValue(idx: number, value?: FilterValue) {
  if (value === undefined) {
    // Remove from current view only, do not touch localStorage
    activeFilters.value = activeFilters.value.filter((_, i) => i !== idx);
  } else {
    const newValue = [...activeFilters.value];
    newValue[idx] = value;
    activeFilters.value = newValue;
  }
}
</script>

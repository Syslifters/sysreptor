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
import { onMounted, watch } from 'vue';
import { usePinnedFilters } from '@/composables/usePinnedFilters';

const props = defineProps<{
  filterProperties: FilterProperties[];
}>();

// activeFilters is a model bound from parent
const activeFilters = defineModel<FilterValue[]>({ required: true });

const { getPinnedFilters, restorePinnedFilters } = usePinnedFilters();

function mergePinnedIntoActive() {
  const pinned = restorePinnedFilters(props.filterProperties);
  if (!pinned || pinned.length === 0) return;
  const merged = [...activeFilters.value];
  let changed = false;
  for (const p of pinned) {
    if (!merged.some(f => f.id === p.id && JSON.stringify(f.value) === JSON.stringify(p.value))) {
      merged.push(p);
      changed = true;
    }
  }
  if (changed) {
    activeFilters.value = merged;
  }
}

onMounted(() => {
  mergePinnedIntoActive();
});

watch(() => props.filterProperties, () => {
  mergePinnedIntoActive();
}, { deep: true });

// Also attempt to merge when parent initializes activeFilters (watch model)
watch(activeFilters, () => {
  mergePinnedIntoActive();
}, { immediate: true, deep: true });

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

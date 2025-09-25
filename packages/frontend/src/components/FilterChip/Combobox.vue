<template>
  <filter-chip-base
    v-model:filter="filter"
    :filter-properties="props.filterProperties"
    @remove="emit('remove')"
  >
    <s-combobox
      v-model="filter.value"
      :label="props.filterProperties.name || filter.id"
      :items="items"
      density="compact"
      spellcheck="false"
      :multiple="false"
      clearable
      v-intersect="loadItems"
    />
  </filter-chip-base>
</template>

<script setup lang="ts">
import { isFunction } from 'lodash-es';

const filter = defineModel<FilterValue>('filter', { required: true })
const props = defineProps<{
  filterProperties: FilterProperties
}>()
const emit = defineEmits(['remove']);

const items = ref<string[]|any[]>([]);
const itemsLoaded = ref(false);
async function loadItems() {
  try {
    items.value = await Promise.resolve(isFunction(props.filterProperties.options) ? props.filterProperties.options() : props.filterProperties.options || []);
  } catch{
    // Ignore errors
  } finally {
    itemsLoaded.value = true;
  }
}
</script>

<template>
  <filter-chip-base
    v-model:filter="filter"
    :display-value="displayValue"
    :filter-properties="props.filterProperties"
    @remove="emit('remove')"
  >
    <s-select
      v-model="filter.value"
      :label="props.filterProperties.name || filter.id"
      :items="items || []"
      item-title="title"
      item-value="value"
      density="compact"
      :multiple="false"
    >
      <template #item="{ props: itemProps, item }">
        <v-list-item v-bind="itemProps">
          <template #prepend v-if="item.raw?.icon">
            <v-icon>{{ item.raw.icon }}</v-icon>
          </template>
        </v-list-item>
      </template>
      
      <template #selection="{ item }">
        <div class="d-flex align-center">
          <v-icon v-if="item.raw?.icon" class="me-2" size="small">
            {{ item.raw.icon }}
          </v-icon>
          {{ displayValue }}
        </div>
      </template>
    </s-select>
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
onMounted(async () => {
  items.value = await Promise.resolve(isFunction(props.filterProperties.options) ? props.filterProperties.options() : props.filterProperties.options || []);
});

const displayValue = computed(() => {
  if (!filter.value.value) { 
    return '';
  }
  const selectedItem = items.value.find(item => {
    if (typeof item === 'string') {
      return item === filter.value.value;
    } else {
      return item.value === filter.value.value;
    }
  });

  if (!selectedItem) {
    return String(filter.value.value);
  } else if (typeof selectedItem === 'object' && selectedItem.title) {
    return selectedItem.title;
  } else {
    return selectedItem;
  }
});
</script>

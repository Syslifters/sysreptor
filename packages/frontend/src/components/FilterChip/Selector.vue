<template>
  <s-btn-icon>
    <v-icon icon="mdi-filter-plus-outline" />

    <v-menu
      v-if="props.filterProperties && props.filterProperties.length"
      activator="parent"
      location="bottom"
    >
      <v-list>
        <v-list-item
          v-for="filter in filterProperties"
          :key="filter.id"
          :title="filter.name"
          :prepend-icon="filter.icon || 'mdi-filter'"
          @click="addFilter(filter.id)"
          :disabled="activeFilters.some(activeFilter => activeFilter.id === filter.id) && !filter.multiple"
        />
      </v-list>
    </v-menu>
  </s-btn-icon>
</template>

<script setup lang="ts">
const activeFilters = defineModel<FilterValue[]>('activeFilters', { required: true });
const props = defineProps<{
  filterProperties: FilterProperties[];
}>();

function addFilter(filterId: string) {
  activeFilters.value = activeFilters.value.concat([{
    id: filterId,
    value: props.filterProperties.find(filter => filter.id === filterId)?.default || '',
    exclude: false,
    regex: false,
  }]);
}

</script>

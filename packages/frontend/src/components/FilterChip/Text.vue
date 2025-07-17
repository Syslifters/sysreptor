<template>
  <filter-chip-base
    v-model:filter="filter"
    :filter-properties="props.filterProperties"
    :display-value="displayValue"
    @remove="emit('remove')"
  >
    <v-text-field
      v-model="filter.value"
      :label="props.filterProperties.name || filter.id"
      variant="outlined"
      density="compact"
      hide-details="auto"
      spellcheck="false"
      clearable
    />
    <div class="d-flex align-center justify-left mt-1 ml-4">
      <v-checkbox
        v-if="props.filterProperties.allow_regex"
        v-model="filter.regex"
        label="Regex"
        density="compact"
        hide-details
        class="mt-2"
      />
    </div>
  </filter-chip-base>
</template>

<script setup lang="ts">
const filter = defineModel<FilterValue>('filter', { required: true })
const props = defineProps<{
  filterProperties: FilterProperties
}>();
const emit = defineEmits(['remove']);

const displayValue = computed(() => {
  if (typeof filter.value.value === 'string' && filter.value.value.length) {
    return filter.value.value
  } else {
    return 'Any'
  }
})
</script>

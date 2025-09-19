<template>
  <v-chip
    class="mr-2 mb-2"
    color="primary"
    variant="tonal"
    closable
    @click:close="emit('remove')"
  >
    <v-icon v-if="props.filterProperties.icon" start size="small" :icon="props.filterProperties.icon" />
    {{ filter.exclude ? '! ' : '' }}{{ props.filterProperties.name }}: {{ chipDisplayValue }}
    <v-icon v-if="isPinned" icon="mdi-pin" size="small" class="ml-1" />

    <slot name="chip-actions"></slot>

    <v-menu
      activator="parent"
      :close-on-content-click="false"
      location="bottom"
    >
      <v-card :min-width="props.minWidth || '250px'">
        <v-card-text>
          <slot name="default"></slot>
          <div
            v-if="props.filterProperties.allow_exclude || isPinned !== undefined"
            class="d-flex align-center justify-left mt-1"
          >
            <v-switch
              v-if="props.filterProperties.allow_exclude"
              v-model="filter.exclude"
              color="secondary"
              hide-details
              density="compact"
              class="mr-2 ml-4"
            >
              <template #label>
                <label>
                  {{ filter.exclude ? 'Exclude' : 'Include' }}
                </label>
              </template>
            </v-switch>
            <v-spacer />

            <v-checkbox-btn
              v-if="isPinned !== undefined"
              v-model="isPinned"
              true-icon="mdi-pin"
              false-icon="mdi-pin-off"
              density="compact"
              inline
              v-tooltip="{text: 'Pin filter to persist across sessions'}"
            />
          </div>
        </v-card-text>
      </v-card>
    </v-menu>
  </v-chip>
</template>

<script setup lang="ts">
import { cloneDeep, isEqual } from 'lodash-es';

const filter = defineModel<FilterValue>('filter', { required: true });
const isPinned = defineModel<boolean>('isPinned');
const props = defineProps<{
  filterProperties: FilterProperties;
  displayValue?: string;
  minWidth?: string;
}>();
const emit = defineEmits(['remove']);

const chipDisplayValue = computed(() => {
  if (props.displayValue) {
    return props.displayValue
  }
  if (typeof filter.value.value === 'string' && filter.value.value) {
    return filter.value.value
  } else if (Array.isArray(filter.value.value)) {
    return filter.value.value.join(', ')
  } else {
    return 'Any'
  }
})

const oldFilterValue = ref<FilterValue>(cloneDeep(filter.value));
watch(filter, () => {
  // Trigger update:filter events when a sub-property changes
  if (oldFilterValue.value.internalId === filter.value.internalId && !isEqual(oldFilterValue.value, filter.value)) {
    oldFilterValue.value = cloneDeep(toValue(filter.value));
    filter.value = {...filter.value};
  }
}, { deep: true });
</script>

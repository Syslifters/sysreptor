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
    <v-icon
      class="ml-1"
      size="small"
      :icon="props.isPinned ? 'mdi-pin' : 'mdi-pin-off'"
      @click.stop="togglePin"
      title="Pin filter to persist across sessions"
    />
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
            v-if="props.filterProperties.allow_exclude"
            class="d-flex align-center justify-left mt-1"
          >
            <v-switch
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
          </div>
        </v-card-text>
      </v-card>
    </v-menu>
  </v-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const filterId = computed(() => {
  // Unique identifier for the filter: use property id to avoid display-name changes
  return `${props.filterProperties.id}:${JSON.stringify(filter.value.value)}`;
});

function togglePin() {
  // Emit pin/unpin events upward; parent will update the store
  if (props.isPinned) {
    emit('unpin', filterId.value);
  } else {
    emit('pin', filterId.value);
  }
}
const filter = defineModel<FilterValue>('filter', { required: true });
const props = defineProps<{
  filterProperties: FilterProperties;
  displayValue?: string;
  minWidth?: string;
  isPinned?: boolean;
}>();
const emit = defineEmits(['remove', 'pin', 'unpin']);

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
</script>

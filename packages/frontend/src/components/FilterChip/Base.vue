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
      :icon="isPinned ? 'mdi-pin' : 'mdi-pin-off'"
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
import { ref, watch, onMounted } from 'vue';

const PINNED_FILTERS_KEY = 'pinnedFilters';

function getPinnedFilters() {
  try {
    return JSON.parse(localStorage.getItem(PINNED_FILTERS_KEY) || '[]');
  } catch {
    return [];
  }
}

function setPinnedFilters(filters: string[]) {
  localStorage.setItem(PINNED_FILTERS_KEY, JSON.stringify(filters));
}

const filterId = computed(() => {
  // Unique identifier for the filter (customize as needed)
  return `${props.filterProperties.name}:${JSON.stringify(filter.value.value)}`;
});

const isPinned = ref(false);

function togglePin() {
  const pinned = getPinnedFilters();
  if (isPinned.value) {
  const newPinned = pinned.filter((f: string) => f !== filterId.value);
  setPinnedFilters(newPinned);
    isPinned.value = false;
    console.debug('[FilterChip] unpinned', { filterId: filterId.value, pinnedBefore: pinned, pinnedAfter: newPinned });
  } else {
    const newPinned = [...pinned, filterId.value];
    setPinnedFilters(newPinned);
    isPinned.value = true;
    console.debug('[FilterChip] pinned', { filterId: filterId.value, pinnedBefore: pinned, pinnedAfter: newPinned });
  }
}

onMounted(() => {
  const pinned = getPinnedFilters();
  isPinned.value = pinned.includes(filterId.value);
  console.debug('[FilterChip] mounted', { filterId: filterId.value, pinned });
});

watch(filterId, (newId) => {
  const pinned = getPinnedFilters();
  isPinned.value = pinned.includes(newId);
  console.debug('[FilterChip] filterId changed', { newId, pinned });
});
const filter = defineModel<FilterValue>('filter', { required: true });
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
</script>

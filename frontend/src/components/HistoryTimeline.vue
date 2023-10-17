<template>
  <v-navigation-drawer
    :model-value="props.modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    location="right"
    absolute
    temporary
    class="history-sidebar"
  >
    <div class="history-timeline-header">
      <v-list-item>
        <v-list-item-title class="text-h6">
          Version History
        </v-list-item-title>
        <template #append>
          <v-btn icon variant="text" @click="emit('update:modelValue', false)">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>

    <v-list-item v-if="!apiSettings.isProfessionalLicense">
      Version history is not available <br>
      in community edition.<br><br>
      See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank">https://docs.sysreptor.com/features-and-pricing/</a>
    </v-list-item>
    <div v-else>
      <v-timeline
        direction="vertical"
        side="end"
        align="start"
        density="compact"
        :truncate-line="historyRecords.hasNextPage.value ? 'start' : 'both'"
        class="history-timeline-content"
      >
        <history-timeline-item
          v-if="props.currentUrl"
          :value="{history_type: '~', history_change_reason: 'Current Version'}"
          :to="currentUrl"
        >
          <template #info><span /></template>
        </history-timeline-item>
        <slot name="item" v-for="item in historyRecords.data.value" :item="item">
          <history-timeline-item :value="item" />
        </slot>
      </v-timeline>
      <page-loader :items="historyRecords" />
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean;
  url: string;
  currentUrl?: string|null;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const apiSettings = useApiSettings();

const historyRecords = useSearchableCursorPaginationFetcher({
  baseURL: props.url
});
function resetHistoryRecords() {
  historyRecords.reset({ baseURL: props.url });
}
watch(() => props.modelValue, () => {
  if (props.modelValue) {
    resetHistoryRecords();
  }
});
watch(() => props.url, () => {
  resetHistoryRecords();
  if (props.modelValue) {
    emit('update:modelValue', false);
  }
});
</script>

<style lang="scss" scoped>
.history-sidebar {
  width: 25em !important;
}

.history-timeline-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white;
}
.history-timeline-content {
  grid-row-gap: 0;
  padding-left: 0.5em;
}
</style>

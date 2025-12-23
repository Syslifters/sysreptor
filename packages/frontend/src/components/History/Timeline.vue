<template>
  <v-navigation-drawer
    v-if="mobile ? modelValue : true"
    v-model="modelValue"
    location="right"
    temporary
    touchless
    :mobile-breakpoint="0" 
    class="history-sidebar"
  >
    <div class="history-timeline-header">
      <v-list-item class="pt-0 pb-0">
        <v-list-item-title class="text-h6">
          <pro-info>Version History</pro-info>
        </v-list-item-title>
        <template #append>
          <v-btn icon variant="text" @click="modelValue = false">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>

    <v-list-item v-if="!apiSettings.isProfessionalLicense">
      Version history is available<br>
      in SysReptor Professional.<br><br>
      See <a href="https://sysreptor.com/pricing" target="_blank" class="text-primary">https://sysreptor.com/pricing</a>
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
          :value="{history_type: '~', history_change_reason: 'Current Version'} as unknown as HistoryTimelineRecord"
          :to="currentUrl"

        >
          <template #info><span /></template>
        </history-timeline-item>
        <template v-for="item, idx in historyRecords.data.value" :key="idx">
          <slot v-if="!(idx === 0 && item.history_type === '~' && !item.history_change_reason)" name="item" :item="item">
            <history-timeline-item :value="item" />
          </slot>
        </template>
      </v-timeline>
      <page-loader :items="historyRecords" />
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
const modelValue = defineModel<boolean>();

const props = defineProps<{
  url: string;
  currentUrl?: string|null;
}>();

const apiSettings = useApiSettings();
const { mobile } = useDisplay();

const historyRecords = useSearchableCursorPaginationFetcher<HistoryTimelineRecord>({
  baseURL: props.url
});
function resetHistoryRecords() {
  historyRecords.reset({ baseURL: props.url });
}
watch(modelValue, () => {
  if (modelValue.value) {
    resetHistoryRecords();
  }
});
watch(() => props.url, () => {
  resetHistoryRecords();
  modelValue.value = false;
});
</script>

<style lang="scss" scoped>
@use "@base/assets/vuetify.scss" as vuetify;

.history-sidebar {
  z-index: 2001 !important;
}
.history-sidebar + .v-navigation-drawer__scrim {
  z-index: 2000 !important;
}
.history-sidebar.v-navigation-drawer--active {
  width: 25em !important;
}

.history-timeline-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: vuetify.$navigation-drawer-background;
}
.history-timeline-content {
  grid-row-gap: 0;
  padding-left: 0.5em;
}
</style>

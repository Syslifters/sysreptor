<template>
  <list-view :url="apiSettings.isProfessionalLicense ? `/api/v1/pentestprojects/${project.id}/history-timeline/?mode=medium` : null">
    <template #title>
      <pro-info>Version History</pro-info>
    </template>
    <template #searchbar>
      <!-- hide searchbar -->
      <span />
    </template>
    <template #items="{ items }">
      <v-timeline
        v-if="apiSettings.isProfessionalLicense"
        direction="vertical"
        side="end"
        align="start"
        density="compact"
        :truncate-line="items.hasNextPage.value ? 'start' : 'both'"
        class="history-timeline-content"
      >
        <history-timeline-item
          :value="{history_type: '~', history_change_reason: 'Current Version'} as unknown as HistoryTimelineRecord"
          :to="`/projects/${project.id}/reporting/`"
        >
          <template #info><span /></template>
        </history-timeline-item>
        <history-timeline-item-project 
          v-for="item in (items.data.value as HistoryTimelineRecord[])" 
          :key="item.id" 
          :item="item" 
          :project="project" 
          :details="true"
        />
      </v-timeline>
      <v-list-item v-else>
        Version history is available in SysReptor Professional.<br><br>
        See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank" class="text-primary">https://docs.sysreptor.com/features-and-pricing/</a>
      </v-list-item>
    </template>
  </list-view>
</template>

<script setup lang="ts">
const route = useRoute();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const project = await useAsyncDataE(() => projectStore.getById(route.params.projectId as string));
</script>

<style lang="scss" scoped>
.history-timeline-content {
  grid-row-gap: 0;
  padding-left: 0.5em;
}
</style>

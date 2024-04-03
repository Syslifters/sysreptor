<template>
  <div v-if="statusInfo && statusInfo.value !== ReviewStatus.IN_PROGRESS" class="status-icon">
    <v-icon size="small" :class="'status-' + statusInfo.value" :icon="statusInfo.icon" />
    <s-tooltip activator="parent" :text="statusInfo.title" />
  </div>
</template>

<script setup lang="ts">
import { ReviewStatus } from "~/utils/types";

const props = defineProps<{
  value?: ReviewStatus|null;
}>();
const statusInfo = computed(() => ReviewStatusItems.find(i => i.value === props.value)!);
</script>

<style lang="scss" scoped>
@use "@/assets/settings" as settings;

.status-icon {
  margin-left: 0 !important;
  min-width: 1em !important;
}

.status-finished {
  color: settings.$status-color-finished !important;
}

</style>

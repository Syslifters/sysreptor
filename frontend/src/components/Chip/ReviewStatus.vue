<template>
  <v-chip v-if="statusInfo" size="small" class="ma-1">
    <v-icon size="small" start :class="'status-' + statusInfo.value" :icon="statusInfo.icon" />
    {{ statusInfo.title }}
  </v-chip>
</template>

<script setup lang="ts">
import { ProjectTypeStatus, ReviewStatus } from '@/utils/types';

const props = defineProps<{
  value?: ReviewStatus|ProjectTypeStatus|null
}>();
const statusInfo = computed(() => ProjectTypeStatusItems.find(i => i.value === props.value))
</script>

<style lang="scss" scoped>
@use "@/assets/settings.scss" as settings;

.status-finished {
  color: settings.$status-color-finished !important;
}
.status-deprecated {
  color: settings.$status-color-deprecated !important;
}
</style>

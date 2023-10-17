<template>
  <v-chip v-if="statusInfo" size="small" class="ma-1">
    <v-icon size="small" start :class="'status-' + statusInfo.value" :icon="statusInfo.icon" />
    {{ statusInfo.title }}
  </v-chip>
</template>

<script setup lang="ts">
import { ReviewStatusItems } from "~/utils/types";

const props = defineProps<{
  value?: string|null
}>();
const statusInfo = computed(() => ReviewStatusItems.find(i => i.value === props.value))
</script>

<style lang="scss" scoped>
@use "@/assets/settings.scss" as settings;

.status-finished {
  color: settings.$status-color-finished !important;
}
</style>

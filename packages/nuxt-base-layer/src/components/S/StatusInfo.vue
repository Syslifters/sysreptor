<template>
  <div v-if="statusInfo && statusInfo.id !== ReviewStatus.IN_PROGRESS" class="status-icon">
    <v-icon size="small" :class="'status-' + statusInfo.id" :icon="statusInfo.icon || 'mdi-help'" />
    <s-tooltip activator="parent" :text="statusInfo.label" />
  </div>
</template>

<script setup lang="ts">
import { ReviewStatus } from "#imports";

const props = defineProps<{
  value?: string|null;
}>();

const apiSettings = useApiSettings();
const statusInfo = computed(() => apiSettings.getStatusDefinition(props.value));
</script>

<style lang="scss" scoped>
@use "@base/assets/settings" as settings;

.status-icon {
  margin-left: 0;
  min-width: 1em;
}

.status-finished {
  color: settings.$status-color-finished;
}

</style>

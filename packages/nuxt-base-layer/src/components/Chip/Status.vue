<template>
  <v-chip v-if="statusInfo" size="small" class="ma-1">
    <v-icon size="small" start :class="'status-' + statusInfo.id" :icon="statusInfo.icon || 'mdi-help'" />
    {{ statusInfo.label }}
  </v-chip>
</template>

<script setup lang="ts">
const props = defineProps<{
  value?: string|null
}>();

const apiSettings = useApiSettings();
const statusInfo = computed(() => apiSettings.getStatusDefinition(props.value));
</script>

<style lang="scss" scoped>
@use "@base/assets/settings.scss" as settings;

.status-finished {
  color: settings.$status-color-finished !important;
}
.status-deprecated {
  color: settings.$status-color-deprecated !important;
}
</style>

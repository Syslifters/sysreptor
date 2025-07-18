<template>
  <v-chip v-if="statusInfo" size="small" class="ma-1">
    <v-icon size="small" start :class="'status-' + statusInfo.id" :icon="statusInfo.icon || 'mdi-help'" />
    {{ statusInfo.label }}
    <v-icon 
      v-if="props.filterable" 
      size="small" 
      end 
      icon="mdi-filter-variant" 
      @click.stop.prevent="applyFilter"
      class="ml-1 filter-icon"
    />
  </v-chip>
</template>

<script setup lang="ts">
const props = defineProps<{
  value?: string|null;
  filterable?: boolean;
}>();

const emit = defineEmits<{
  filter: [filter: FilterValue];
}>();

const apiSettings = useApiSettings();
const statusInfo = computed(() => apiSettings.getStatusDefinition(props.value));

function applyFilter() {
  if (props.value) {
    emit('filter', {
      id: 'status',
      value: props.value,
      exclude: false,
      regex: false
    });
  }
}
</script>

<style lang="scss" scoped>
@use "@base/assets/settings.scss" as settings;

.status-finished {
  color: settings.$status-color-finished !important;
}
.status-deprecated {
  color: settings.$status-color-deprecated !important;
}

.filter-icon {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
  
  &:hover {
    opacity: 1;
  }
}
</style>

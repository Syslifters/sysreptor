<template>
  <v-select
    v-model="modelValue"
    :items="statusItems"
    label="Status"
    item-value="id"
    item-title="label"
    hide-details="auto"
    :variant="props.variant"
    :density="props.density"
    data-testid="status-select"
  >
    <template #item="{item: { raw: statusInfo }, props: itemProps}">
      <v-list-item v-bind="itemProps" :data-testid="'status-' + statusInfo.id">
        <template #prepend>
          <v-icon :class="'status-' + statusInfo.id" :icon="statusInfo.icon || 'mdi-help'" />
        </template>
      </v-list-item>
    </template>
    <template #selection="{item: { raw: statusInfo }}">
      <v-icon start :class="'status-' + statusInfo.id" :icon="statusInfo.icon || 'mdi-help'" :data-testid="'status-' +  statusInfo" /> 
      {{ statusInfo.label }}
    </template>
  </v-select>
</template>

<script setup lang="ts">
import { VSelect } from "vuetify/lib/components/index.mjs";
import { ReviewStatus } from "#imports";

const modelValue = defineModel<string|null>();
const props = withDefaults(defineProps<{
  includeDeprecated?: boolean;
  variant?: VSelect['variant'];
  density?: VSelect['density'];
}>(), {
  includeDeprecated: false,
  variant: 'underlined',
  density: 'compact'
});

const apiSettings = useApiSettings();
const previousStatuses = ref<string[]>([]);
const statusItems = computed(() => {
  const items = [];
  items.push(...(apiSettings.settings?.statuses || []));
  if (props.includeDeprecated) {
    items.push(apiSettings.getStatusDefinition(ReviewStatus.DEPRECATED));
  }

  // Include unknown statuses
  for (const s of previousStatuses.value) {
    if (!items.some(item => item.id === s)) {
      items.push(apiSettings.getStatusDefinition(s));
    }
  }
  return items;
});

watch(() => modelValue, () => {
  if (modelValue.value && !previousStatuses.value.includes(modelValue.value)) {
    previousStatuses.value.push(modelValue.value);
  }
}, { immediate: true });

</script>

<style lang="scss" scoped>
@use "@base/assets/settings" as settings;

:deep(.v-select__selection) {
  white-space: nowrap;
  overflow: hidden;
}


.status-finished {
  color: settings.$status-color-finished !important;
}
.status-deprecated {
  color: settings.$status-color-deprecated !important;
}
</style>

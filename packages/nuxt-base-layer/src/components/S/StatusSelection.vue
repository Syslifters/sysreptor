<template>
  <v-select
    v-model="modelValue"
    :items="statusItems"
    label="Status"
    item-value="id"
    item-title="label"
    item-props="props"
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
import { ReviewStatus, type ReviewStatusDefinition } from "#imports";

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
const auth = useAuth();

const previousStatuses = ref<string[]>([]);
const statusItems = computed(() => {
  const allItems = [] as (ReviewStatusDefinition & { props?: any })[];
  allItems.push(...(apiSettings.settings?.statuses || []));
  if (props.includeDeprecated) {
    allItems.push(apiSettings.getStatusDefinition(ReviewStatus.DEPRECATED));
  }

  // Include unknown statuses from previous values
  for (const s of previousStatuses.value) {
    if (!allItems.some(item => item.id === s)) {
      allItems.push(apiSettings.getStatusDefinition(s));
    }
  }

  // Filter based on allowed transitions
  const currentStatusDefinition = apiSettings.getStatusDefinition(modelValue.value);
  if ((currentStatusDefinition.allowed_next_statuses?.length || 0) > 0 && !auth.permissions.value.admin) {
    allItems.forEach(s => {
      s.props = {
        disabled: !(currentStatusDefinition.allowed_next_statuses?.includes(s.id) || s.id === currentStatusDefinition.id),
      }
    })
  }
  return allItems;
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

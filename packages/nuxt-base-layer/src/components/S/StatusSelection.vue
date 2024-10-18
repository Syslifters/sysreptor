<template>
  <v-select
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :items="props.items"
    label="Status"
    hide-details="auto"
    :variant="props.variant"
    :density="props.density"
  >
    <template #item="{item: { raw: statusInfo }, props: itemProps}">
      <v-list-item v-bind="itemProps">
        <template #prepend>
          <v-icon :class="'status-' + statusInfo.value" :icon="statusInfo.icon" />
        </template>
      </v-list-item>
    </template>
    <template #selection="{item: { raw: statusInfo }}">
      <v-icon start :class="'status-' + statusInfo.value" :icon="statusInfo.icon" /> {{ statusInfo.title }}
    </template>
  </v-select>
</template>

<script setup lang="ts">
import { VSelect } from "vuetify/lib/components/index.mjs";
import type { ReviewStatus, ProjectTypeStatus } from "#imports";

const props = withDefaults(defineProps<{
  modelValue?: ReviewStatus|ProjectTypeStatus|null;
  items?: typeof ReviewStatusItems|typeof ProjectTypeStatusItems;
  variant?: VSelect['variant'];
  density?: VSelect['density'];
}>(), {
  modelValue: null,
  items: () => ReviewStatusItems,
  variant: 'underlined',
  density: 'compact'
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: ReviewStatus|ProjectTypeStatus): void;
}>();
</script>

<style lang="scss" scoped>
@use "@base/assets/settings" as settings;

.status-finished {
  color: settings.$status-color-finished !important;
}
.status-deprecated {
  color: settings.$status-color-deprecated !important;
}
</style>

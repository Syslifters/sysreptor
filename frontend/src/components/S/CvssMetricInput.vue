<template>
  <v-radio-group
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :disabled="props.disabled"
    inline
  >
    <template #label>
      <span class="label-tooltip">
        {{ metric.name }} ({{ metric.id }})
        <s-tooltip activator="parent" v-bind="tooltipAttrs" :text="metric.description" />
      </span>
    </template>

    <v-radio v-for="c in metric.choices" :value="c.id" :key="metric.id + '_' + c.id" color="primary">
      <template #label>
        <span class="label-tooltip">
          {{ c.name }} ({{ c.id }})
          <s-tooltip activator="parent" :text="c.description" v-bind="tooltipAttrs" />
        </span>
      </template>
    </v-radio>
  </v-radio-group>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: string;
  metric: CvssMetricDefinition;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const tooltipAttrs = {
  openDelay: 1000,
  location: 'bottom',
}
</script>

<style lang="scss" scoped>
.label-tooltip {
  cursor: help;
}
</style>

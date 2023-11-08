<template>
  <div class="d-flex ma-1" :class="{'flex-row': props.singleLine, 'flex-column': !props.singleLine}">
    <v-label class="cvss-metric-label" :class="{'cvss-metric-label-inline': props.singleLine}">
      <div class="cvss-metric-label-text">{{ metric.name }}</div>
      <s-tooltip activator="parent" :text="metric.description" v-bind="tooltipAttrs" />
    </v-label>
    <div>
      <v-btn-toggle
        :model-value="props.modelValue"
        @update:model-value="emit('update:modelValue', $event)"
        :disabled="props.disabled"
        mandatory
        density="compact"
        :border="true"
        color="primary"
      >
        <v-btn 
          v-for="c in metric.choices" 
          :key="metric.id + '_' + c.id" 
          :value="c.id" 
          size="small" 
          class="metric-btn"
        >
          {{ c.name }} ({{ c.id }})
          <s-tooltip activator="parent" :text="c.description" v-bind="tooltipAttrs" />
        </v-btn>
      </v-btn-toggle>
    </div>
  </div>
  <!-- <v-radio-group
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
  </v-radio-group> -->
</template>

<script setup lang="ts">
import { CvssMetricDefinition } from '~/utils/cvss/base';

const props = defineProps<{
  modelValue: string;
  metric: CvssMetricDefinition;
  singleLine?: boolean;
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
.cvss-metric-label {
  min-width: 15em;
  cursor: help;

  &-inline {
    .cvss-metric-label-text {
      display: inline-block;
      width: 100%;
      padding-right: 1em;
      text-align: end;
    }
  }
}
.metric-btn {
  min-width: 10em;
}
</style>

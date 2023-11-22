<template>
  <div class="ma-1" :class="{'metric-inline': props.singleLine, 'metric-twoline': !props.singleLine}">
    <v-label class="metric-label">
      <div class="metric-label-text">{{ metric.name }}</div>
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
</template>

<script setup lang="ts">
import type { CvssMetricDefinition } from '~/utils/cvss/base';

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
@use "@/assets/vuetify" as vuetify;

.metric-label {
  cursor: help;
}

.metric-twoline, .metric-inline {
  display: flex;
  flex-direction: column;
}

@media #{map-get(vuetify.$display-breakpoints, 'lg-and-up')} {
  .metric-inline {
    flex-direction: row;

    .metric-label {
      min-width: 15em;
      
      .metric-label-text {
        display: inline-block;
        width: 100%;
        padding-right: 1em;
        text-align: end;
      }
    }

    .metric-btn {
      min-width: 10em;
    }
  }
}
</style>

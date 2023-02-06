<template>
  <div>
    <s-tooltip v-bind="tooltipAttrs">
      <template #activator="{ on, attrs }">
        <p class="label-tooltip" v-bind="attrs" v-on="on">
          {{ metric.name }} ({{ metric.id }})
        </p>
      </template>
      <template #default>
        <span>{{ metric.description }}</span>
      </template>
    </s-tooltip>

    <v-radio-group :value="value" @change="$emit('input', $event)" :disabled="disabled" row>
      <template v-for="c in metric.choices">
        <v-radio :value="c.id" :key="metric.id + '_' + c.id">
          <template #label>
            <s-tooltip v-bind="tooltipAttrs">
              <template #activator="{ on, attrs }">
                <span class="label-tooltip" v-bind="attrs" v-on="on">{{ c.name }} ({{ c.id }})</span>
              </template>
              <template #default>
                <span>{{ c.description }}</span>
              </template>
            </s-tooltip>
          </template>
        </v-radio>
      </template>
    </v-radio-group>
  </div>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      required: true,
    },
    metric: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  emits: ['input'],
  data() {
    return {
      tooltipAttrs: {
        openDelay: 1000,
        bottom: true,
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.label-tooltip {
  cursor: help;
}
</style>

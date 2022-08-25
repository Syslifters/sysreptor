<template>
  <div>
    <s-tooltip v-bind="tooltipAttrs">
      <template #activator="{ on, attrs }">
        <p v-bind="attrs" v-on="on">
          {{ metric.name }} ({{ metric.id }})
        </p>
      </template>
      <template #default>
        <span>{{ metric.description }}</span>
      </template>
    </s-tooltip>

    <v-radio-group :value="value" @change="$emit('input', $event)" :disabled="disabled" row>
      <template v-for="c in metric.choices">
        <s-tooltip :key="metric.id + '_' + c.id" v-bind="tooltipAttrs">
          <template #activator="{ on, attrs }">
            <v-radio :value="c.id" v-bind="attrs" v-on="on">
              <template #label>
                {{ c.name }} ({{ c.id }})
              </template>
            </v-radio>
          </template>
          <template #default>
            <span>{{ c.description }}</span>
          </template>
        </s-tooltip>
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
        // openDelay: 500,
        bottom: true,
      }
    }
  }
}
</script>

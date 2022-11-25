<template>
  <s-tooltip v-if="statusInfo && statusInfo.value !== 'in-progress'">
    <template #activator="{on, attrs}">
      <v-list-item-icon v-on="on" v-bind="attrs" class="status-icon">
        <v-icon small :class="'status-' + statusInfo.value" v-on="on" v-bind="attrs">{{ statusInfo.icon }}</v-icon>
      </v-list-item-icon>
    </template>

    <template #default>{{ statusInfo.text }}</template>
  </s-tooltip>
</template>

<script>
import { ReviewStatusItems } from './StatusSelection.vue'

export default {
  props: {
    value: {
      type: String,
      required: true,
    }
  },
  computed: {
    statusInfo() {
      return ReviewStatusItems.find(i => i.value === this.value);
    }
  }
}
</script>

<style lang="scss" scoped>
.status-icon {
  margin-left: 0 !important;
  min-width: 1em !important;
}

.status-finished {
  color: $status-color-finished !important;
}

</style>

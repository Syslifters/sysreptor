<template>
  <v-chip v-if="statusInfo" small>
    <v-icon small left :class="'status-' + statusInfo.value">{{ statusInfo.icon }}</v-icon>
    {{ statusInfo.text }}
  </v-chip>
</template>

<script>
import { ReviewStatusItems } from '../StatusSelection.vue'
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
.status-finished {
  color: $status-color-finished !important;
}
</style>

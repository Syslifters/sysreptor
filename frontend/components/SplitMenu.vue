<template>
  <splitpanes @resized="$emit('input', $event[0].size)" class="default-theme">
    <pane :size="value">
      <v-navigation-drawer permanent left width="100%">
        <slot name="menu" />
      </v-navigation-drawer>
    </pane>
    <pane :size="100 - value">
      <v-container fluid>
        <slot name="default" />
      </v-container>
    </pane>
  </splitpanes>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes'

export default {
  components: { Splitpanes, Pane },
  props: {
    value: {
      type: Number,
      default: 15,
    }
  }
}
</script>

<style lang="scss">
@import '@/assets/splitpanes.scss';
</style>

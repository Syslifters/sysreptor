<template>
  <splitpanes @resized="$emit('input', $event[0].size)" class="h-100 default-theme">
    <pane :size="value" class="h-100 overflow-y-auto">
      <v-navigation-drawer permanent left width="100%">
        <slot name="menu" />
      </v-navigation-drawer>
    </pane>
    <pane :size="100 - value" class="h-100 overflow-y-auto">
      <v-container fluid class="pt-0 pb-0">
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

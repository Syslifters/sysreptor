<template>
  <splitpanes @resized="$emit('input', $event[0].size)" class="default-theme">
    <pane :size="value">
      <fill-screen-height>
        <v-navigation-drawer permanent left width="100%">
          <slot name="menu" />
        </v-navigation-drawer>
      </fill-screen-height>
    </pane>
    <pane :size="100 - value">
      <fill-screen-height>
        <v-container fluid class="pt-0 pb-0">
          <slot name="default" />
        </v-container>
      </fill-screen-height>
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

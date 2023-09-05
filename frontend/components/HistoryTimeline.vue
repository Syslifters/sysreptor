<template>
  <v-navigation-drawer 
    v-if="value"
    :value="value" 
    @input="$emit('input', $event)" 
    right
    absolute
    temporary
    width="25em"
  >
    <div class="history-timeline-header">
      <v-list-item>
        <v-list-item-title class="text-h6">
          Version History
        </v-list-item-title>
        <v-list-item-action>
          <v-btn icon @click="$emit('input', false)">
            <v-icon large>mdi-close</v-icon>
          </v-btn>
        </v-list-item-action>
      </v-list-item>
      <v-divider />
    </div>
    
    <v-list-item v-if="!isProfessionalLicense">
      Version history is not availalbe in community edition.<br>
      Upgrade to SysReptor Professional
    </v-list-item>
    <template v-else>
      <v-timeline align-top dense>
        <slot name="item" v-for="item in historyRecords.data" :item="item">
          <history-timeline-item :value="item" />
        </slot>
      </v-timeline>
      <page-loader :items="historyRecords" />
    </template>
  </v-navigation-drawer>
</template>

<script>
import { CursorPaginationFetcher } from '~/utils/urls'; 

export default {
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      historyRecords: null,
    }
  },
  computed: {
    isProfessionalLicense() {
      return this.$store.getters['apisettings/isProfessionalLicense'];
    },
  },
  watch: {
    url: {
      immediate: true,
      handler() {
        this.historyRecords = new CursorPaginationFetcher(this.url, this.$axios, this.$toast);
        if (this.value) {
          this.$emit('input', false);
        }
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.history-timeline-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white;
}
</style>

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
      <v-list-item-content>
        Version history is not availalbe <br>
        in community edition.<br><br>
        See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank">https://docs.sysreptor.com/features-and-pricing/</a>
      </v-list-item-content>
    </v-list-item>
    <template v-else>
      <v-timeline align-top dense>
        <history-timeline-item 
          v-if="currentUrl" 
          :value="{history_type: '~', history_change_reason: 'Current Version'}"
          :to="currentUrl"
        >
          <template #info><span /></template>
        </history-timeline-item>
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
    currentUrl: {
      type: String,
      default: null,
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
        this.reset();
        if (this.value) {
          this.$emit('input', false);
        }
      }
    },
    value() {
      this.reset();
    },
  },
  methods: {
    reset() {
      this.historyRecords = new CursorPaginationFetcher(this.url, this.$axios, this.$toast);
    }
  }
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

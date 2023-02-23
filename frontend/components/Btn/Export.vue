<template>
  <div class="d-flex">
    <v-btn @click="performExport(false)" :loading="actionInProgress" color="secondary" :class="{'btn-left': exportAllUrl !== null}">
      <v-icon>mdi-download</v-icon> Export
    </v-btn>
    <v-menu offset-y left>
      <template #activator="{attrs, on}">
        <v-btn v-if="exportAllUrl" v-bind="attrs" v-on="on" color="secondary" class="btn-right">
          <v-icon>mdi-menu-down</v-icon>
        </v-btn>
      </template>
      <template #default>
        <v-btn @click="performExport(true)" :loading="actionInProgress" color="secondary">
          <v-icon>mdi-download</v-icon> Export with notes
        </v-btn>
      </template>
    </v-menu>
  </div>
</template>

<script>
import fileDownload from 'js-file-download';

export default {
  props: {
    exportUrl: {
      type: String,
      required: true,
    },
    exportAllUrl: {
      type: String,
      default: null,
    },
    name: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      actionInProgress: false,
    };
  },
  computed: {
    filename() {
      const name = (this.name || 'export').replaceAll(' ', '-');
      return name + '.tar.gz';
    },
  },
  methods: {
    async performExport(all = false) {
      if (this.actionInProgress) {
        return;
      }

      try {
        this.actionInProgress = true;
        const res = await this.$axios.$post(all ? this.exportAllUrl : this.exportUrl, {}, {
          responseType: 'arraybuffer',
        });
        fileDownload(res, this.filename);
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProgress = false;
      }
    }
  },
}
</script>

<style lang="scss" scoped>
.btn-left {
  border-radius: $border-radius-root 0 0 $border-radius-root;
  padding-right: 0.5em !important;
}
.btn-right {
  border-radius: 0 $border-radius-root $border-radius-root 0;
  padding-left: 0 !important;
  padding-right: 0 !important;
  min-width: 0 !important;
  margin-left: 1px;
}
</style>

<template>
  <btn-confirm 
    :button-text="buttonText"
    :button-icon="buttonIcon"
    :action="performExport"
    :confirm="false"
    v-bind="$attrs"
  />
</template>

<script>
import fileDownload from 'js-file-download';

export default {
  props: {
    exportUrl: {
      type: String,
      required: true,
    },
    name: {
      type: String,
      default: null,
    },
    buttonText: {
      type: String,
      default: "Export",
    },
    buttonIcon: {
      type: String,
      default: "mdi-download",
    },
  },
  computed: {
    filename() {
      const name = (this.name || 'export').replaceAll(' ', '-');
      return name + '.tar.gz';
    },
  },
  methods: {
    async performExport() {
      const res = await this.$axios.$post(this.exportUrl, {}, {
        responseType: 'arraybuffer',
      });
      fileDownload(res, this.filename);
    }
  }
}
</script>

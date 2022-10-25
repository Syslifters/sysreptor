<template>
  <btn-confirm
    button-text="Export"
    button-icon="mdi-download"
    :confirm="false"
    :action="performExport"
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
  },
}
</script>
